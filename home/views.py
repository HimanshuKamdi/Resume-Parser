from django.shortcuts import render, redirect, HttpResponse
from django.views import View
from django.conf import settings
from .models import PDF, Entity
import fitz
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import os

# import pandas as pd
# import numpy as np
# import plotly.express as px
import re


nlp = spacy.load("en_core_web_lg")
ruler = nlp.add_pipe("entity_ruler", before="ner")
ruler.from_disk("patterns.jsonl")

patterns = [
    {"label": "EMAIL", "pattern": [{"TEXT": {"REGEX": r"\S+@\S+\.\S+"}}]},
    {
        "label": "MOBILE",
        "pattern": [{"TEXT": {"REGEX": r"[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]"}}],
    },
    {
        "label": "MOBILE",
        "pattern": [
            {
                "TEXT": {
                    "REGEX": r"\d{3}[-.\s]??\d{3}[-.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\s]??\d{4}|\d{3}[-.\s]??\d{4}"
                }
            }
        ],
    },
    {
        "label": "MOBILE",
        "pattern": [{"TEXT": {"REGEX": r"^\+?\d{0,3}[-]?\d{3}[-]?\d{4}$"}}],
    },
    {
        "label": "MOBILE",
        "pattern": [
            {
                "TEXT": {
                    "REGEX": r"^\+\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$"
                }
            }
        ],
    },
    {
        "label": "MOBILE",
        "pattern": [{"TEXT": {"REGEX": r"^\+\d{2}-\d{3}-\d{4}-\d{3}$"}}],
    },
    {
        "label": "EDUCATIONAL_INSTITUTION",
        "pattern": [
            {
                "LOWER": {
                    "IN": ["college", "university", "institute", "vidyalaya", "school"]
                }
            },
            {"IS_ALPHA": True, "OP": "*", "IS_STOP": True},
            {"LOWER": {"IN": ["teacher", "professor"]}, "OP": "!"},
            {"IS_ALPHA": True, "OP": "*"},
        ],
    },
    {
        "label": "EDUCATIONAL_INSTITUTION",
        "pattern": [
            {"IS_ALPHA": True, "OP": "*"},
            {
                "LOWER": {
                    "IN": ["college", "university", "institute", "vidyalaya", "school"]
                }
            },
            {"IS_ALPHA": True, "OP": "*", "IS_STOP": True},
            {"LOWER": {"IN": ["teacher", "professor"]}, "OP": "!"},
        ],
    },
    {
        "label": "EDUCATIONAL_INSTITUTION",
        "pattern": [
            {"LOWER": {"REGEX": "(college|university|institute)"}},
            {"IS_ALPHA": True, "OP": "*"},
            {"IS_ALPHA": True, "OP": "*"},
            {"IS_ALPHA": True, "OP": "*"},
            {"IS_ALPHA": True, "OP": "*", "IS_STOP": True},
            {"LOWER": {"IN": ["teacher", "professor"]}, "OP": "!"},
        ],
    },
    # Combine GPE and LOC entities
    {
        "label": "LOCATION",
        "pattern": [
            {"ENT_TYPE": {"IN": ["GPE", "LOC"]}, "OP": "+"},
        ],
    },
    # Combine LANGUAGE and NORP entities
    {
        "label": "LANGUAGE",
        "pattern": [
            {"ENT_TYPE": {"IN": ["LANGUAGE", "NORP"]}},
            {"IS_ALPHA": True, "OP": "+"},
        ],
    },
    {
        "label": "LINKEDIN",
        "pattern": [
            {"LOWER": {"REGEX": r"https?://(www\.)?linkedin\.com/in/[\w\-]+/?$"}}
        ],
    },
    {
        "label": "GITHUB",
        "pattern": [{"LOWER": {"REGEX": r"https?://(www\.)?github\.com/[\w\-]+/?$"}}],
    },
]
ruler.add_patterns(patterns)


class HomeView(View):
    def get(self, request):
        return render(request, "home.html")

    def post(self, request):
        entities_list = []  # Initialize entities list
        entities = {}  # Initialize entities
        images_list = []  # Initialize images list

        if request.method == "POST" and request.FILES["file"]:
            # Get the uploaded file
            uploaded_file = request.FILES["file"]
            pdf_instance = PDF(name=uploaded_file.name)
            pdf_instance.save()

            # Save the file to a temporary location
            file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
            with open(file_path, "wb") as file:
                for chunk in uploaded_file.chunks():
                    file.write(chunk)

            # Create the directory for saving images
            image_dir = os.path.join(settings.MEDIA_ROOT, "static/pdf_images")
            os.makedirs(image_dir, exist_ok=True)

            # Convert PDF to text
            doc = fitz.open(file_path)
            text = ""

            # Iterate over each page of the PDF
            for page_number in range(doc.page_count):
                page = doc.load_page(page_number)

                # Get the image list on the page
                images = page.get_images(full=True)

                # Iterate over each image on the page
                for index, image in enumerate(images):
                    xref = image[0]

                    # Get the image data
                    try:
                        base_image = doc.extract_image(xref)
                        image_data = base_image["image"]

                        # Generate a unique filename for the image
                        filename = (
                            f"static/pdf_images/img_{page_number + 1}_{index}.png"
                        )
                        output_path = os.path.join(settings.MEDIA_ROOT, filename)
                        images_list.append(filename)

                        # Save the image to the output directory
                        with open(output_path, "wb") as image_file:
                            image_file.write(image_data)

                        # print(f"Saved image: {output_path}")
                    except:
                        pass

            for page in doc:
                text += page.get_text("text")

            # Process the text using spaCy model
            texts = " ".join(text.split("\n"))
            print(texts)
            docs = nlp(texts)

            # Function to clean the text and keep only alphabets
            def clean_text(text):
                cleaned_text = re.sub("[^A-Za-z\s]+", " ", text)
                return cleaned_text

            # Function to validate email format
            def is_valid_email(email):
                email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
                return re.match(email_pattern, email) is not None

            # Process the entities
            entity_map = {}

            for ent in docs.ents:
                if ent.label_ in [
                    "PERSON",
                    "ORG",
                    "GPE",
                    "LOC",
                    "LANGUAGES",
                    "SKILL",
                    "DEGREE",
                    "EMAIL",
                    "MOBILE",
                    "EDUCATIONAL_INSTITUTION",
                    "LINKEDIN",
                    "GITHUB",
                ]:
                    label = ent.label_
                    if label == "PERSON":
                        label = "NAME"
                    elif label == "LOC" or label == "GPE":
                        label = "LOCATION"
                    text = ent.text

                    # Clean text and validate based on label
                    if label != "MOBILE" and label != "EMAIL" and label!="LINKEDIN" and label!="GITHUB":
                        text = clean_text(text)
                        text = text.capitalize()
                    elif label == "EMAIL" and not is_valid_email(text):
                        continue

                    # if label in entity_map:
                    #     if label == "NAME":
                    #         continue
                    #     else:
                    #         if text not in entity_map[label]:
                    #             entity_map[label].append(text)
                    #             texts=text.split(" ")
                    #             non_stopwords = [token for token in text if token.lower() not in STOP_WORDS]
                    #             entities_list.extend(non_stopwords)
                    # else:
                    #     entity_map[label] = [text]
                    #     text=text.split(" ")
                    #     non_stopwords = [token for token in text if token.lower() not in STOP_WORDS]
                    #     entities_list.extend(non_stopwords)

                    if label in entity_map:
                        if label == "NAME":
                            continue
                        else:
                            if text not in entity_map[label]:
                                if text.capitalize() not in entity_map[label]:
                                    entity_map[label].append(text)
                                texts = text.split(" ")
                                non_stopwords = [
                                    token.lower()
                                    for token in texts
                                    if token.lower() not in STOP_WORDS
                                ]
                                entities_list.extend(non_stopwords)
                    else:
                        entity_map[label] = [text]
                        texts = text.split(" ")
                        non_stopwords = [
                            token.lower()
                            for token in texts
                            if token.lower() not in STOP_WORDS
                        ]
                        entities_list.extend(non_stopwords)

            # Format entities for display
            for label, texts in entity_map.items():
                combined_text = ",    ".join(texts)
                entities[label] = combined_text

                entity = Entity(pdf=pdf_instance, label=label, text=combined_text)
                entity.save()

            for page in doc:
                words = page.get_text("words")

                for word in words:
                    if word[4].lower() in entities_list:
                        highlight = page.add_highlight_annot(word[:4])
                        highlight.set_colors({"stroke": (0.2, 1, 0.04)})
                        highlight.update()

            annotated_pdf_path = "annotated_pdf.pdf"
            doc.save(annotated_pdf_path)
            doc.close()

            # Delete the temporary file
            os.remove(file_path)

            request.session["entities"] = entities
            request.session["images"] = images_list
            print(entities_list)

            # Redirect to the result page
            return redirect("result")

        return render(request, "home.html")


class ResultView(View):
    def get(self, request):
        entities = request.session.get("entities", {})
        images = request.session.get("images", [])

        # Clear the entities and images from the session
        request.session["entities"] = {}
        request.session["images"] = []

        # pdf_path = "annotated_pdf.pdf"
        # temp_pdf_path = "temp.pdf"

        # # Create a new PDF document
        # doc = fitz.open()

        # # Create the first page with the table
        # page = doc.new_page()

        # # Load the HTML table into the first page
        # table_html = """
        # <html>
        # <head><style>table, th, td {border: 1px solid black; border-collapse: collapse; padding: 5px;}</style></head>
        # <body>
        #   <table class="table">
        #     <tr>
        #       {% if images %}
        #       <td>Images</td>
        #       <td style="display: flex; flex-direction: row; flex-wrap: wrap; justify-content: space-around;">
        #         {% for image in images %}
        #           <img src="{% static image %}" alt="PDF Image" style="height: 200px; width: 200px;">
        #         {% endfor %}
        #       </td>
        #     </tr>
        #     {% endif %}
        #     <tr>
        #       {% if entities.NAME %}
        #       <td>NAME</td>
        #       <td>{{ entities.NAME }}</td>
        #       </tr><tr><td colspan="2"></td></tr>
        #       {% endif %}
        #     </tr>
        #     <tr>
        #       {% if entities.EMAIL %}
        #       <td>EMAIL</td>
        #       <td>{{ entities.EMAIL }}</td>
        #       </tr><tr><td colspan="2"></td></tr>
        #       {% endif %}
        #     </tr>
        #     <tr>
        #       {% if entities.MOBILE %}
        #       <td>MOBILE</td>
        #       <td>{{ entities.MOBILE }}</td>
        #       </tr><tr><td colspan="2"></td></tr>
        #       {% endif %}
        #     </tr>
        #     <tr>
        #       {% if entities.LOCATION %}
        #       <td>LOCATION</td>
        #       <td>{{ entities.LOCATION }}</td>
        #       </tr><tr><td colspan="2"></td></tr>
        #       {% endif %}
        #     </tr>
        #     <tr>
        #       {% if entities.SKILLS %}
        #       <td>SKILLS</td>
        #       <td>{{ entities.SKILLS }}</td>
        #       </tr><tr><td colspan="2"></td></tr>
        #       {% endif %}
        #     </tr>
        #     <tr>
        #       {% if entities.EDUCATIONAL_INSTITUTION %}
        #       <td>EDUCATION</td>
        #       <td>{{ entities.EDUCATIONAL_INSTITUTION }}</td>
        #       </tr><tr><td colspan="2"></td></tr>
        #       {% endif %}
        #     </tr>
        #     <tr>
        #       {% if entities.DEGREE %}
        #       <td>DEGREE</td>
        #       <td>{{ entities.DEGREE }}</td>
        #       </tr><tr><td colspan="2"></td></tr>
        #       {% endif %}
        #     </tr>
        #     <tr>
        #       {% if entities.LANGUAGES %}
        #       <td>LANGUAGES</td>
        #       <td>{{ entities.LANGUAGES }}</td>
        #       </tr><tr><td colspan="2"></td></tr>
        #       {% endif %}
        #     </tr>
        #     <tr>
        #       {% if entities.ORG %}
        #       <td>ORG</td>
        #       <td>{{ entities.ORG }}</td>
        #       </tr><tr><td colspan="2"></td></tr>
        #       {% endif %}
        #     </tr>
        #   </table>
        # </body>
        # </html>
        # """
        # # Insert the table as text using draw_textbox method
        # rect = fitz.Rect(50, 50, 550, 750)  # Adjust the coordinates and size as per your requirement
        # page.insert_textbox(rect, table_html, fontsize=10, align=1)

        # # Append the rest of the pages from the original PDF
        # with open("temp_pdf.pdf", "rb") as orig_pdf:
        #     orig_doc = fitz.open("pdf", orig_pdf.read())
        #     doc.insert_pdf(orig_doc, to_page=1, start_at=1)
        # # with open("temp_pdf.pdf", "rb") as orig_pdf:
        # #  orig_doc = fitz.open("pdf", orig_pdf.read())
        # #  num_pages_orig = orig_doc.page_count

        # #  for page_num in range(1, num_pages_orig + 1):
        # #      page = orig_doc.load_page(page_num)
        # #      doc.insert_page(doc.page_count + 1, width=page.width, height=page.height)
        # #      doc[-1].insert_page(-1, page)

        # # Save the PDF with the inserted table
        # doc.save(temp_pdf_path)
        # doc.close()

        # # Rename the temporary PDF to the desired output path
        # os.rename(temp_pdf_path, pdf_path)

        return render(request, "result.html", {"entities": entities, "images": images})


class DownloadPDFView(View):
    def get(self, request):
        file_path = "annotated_pdf.pdf"  # Path to the generated temp.pdf file

        # Open the file in binary mode for reading
        with open(file_path, "rb") as file:
            response = HttpResponse(file.read(), content_type="application/pdf")
            # Set the content-disposition header to force the browser to download the file
            response["Content-Disposition"] = 'attachment; filename="annotated_pdf.pdf"'
            return response


# df = pd.read_csv("Clean_data.csv")
# df = df.reindex(np.random.permutation(df.index))
# data = df.copy().iloc[0:2000,]


# clean = []
# for i in range(data.shape[0]):
#     review = re.sub(
#         '(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|^rt|http.+?"',
#         " ",
#         data["Resume_str"].iloc[i],
#     )
#     review = review.lower()
#     review = review.split()
#     lm = WordNetLemmatizer()
#     review = [
#         lm.lemmatize(word)
#         for word in review
#         if not word in set(stopwords.words("english"))
#     ]
#     review = " ".join(review)
#     clean.append(review)


# def get_skills(text):
#     doc = nlp(text)
#     myset = []
#     subset = []
#     for ent in doc.ents:
#         if ent.label_ == "SKILL":
#             subset.append(ent.text)
#     myset.append(subset)
#     return subset


# def unique_skills(x):
#     return list(set(x))


# data["Clean_Resume"] = clean
# data["skills"] = data["Clean_Resume"].str.lower().apply(get_skills)
# data["skills"] = data["skills"].apply(unique_skills)
# data.to_csv('Clean_data.csv', index=False)
# print("saved")
# data.head()

# class SkillsView(View):
#     def get(self,request):
#         Job_Category = request.GET.get(
#             "Job_Category"
#         )
#         Total_skills = []
#         if Job_Category != "ALL":
#             fltr = data[data["Category"] == Job_Category]["skills"]
#             for x in fltr:
#                 x=list(x)
#                 # Total_skills=x.split[","]
#                 for i in x:
#                     Total_skills.append(i)
#         else:
#             fltr = data["skills"]
#             for x in fltr:
#                 x=list(x)
#                 Total_skills=x.split[","]
#                 for i in x:
#                     Total_skills.append(i)

#         fig = px.histogram(
#             x=Total_skills,
#             labels={"x": "Skills"},
#             title=f"{Job_Category} Distribution of Skills",
#         ).update_xaxes(categoryorder="total descending")
#         print(Total_skills)

#         # Convert the Plotly figure to HTML and pass it to the template
#         plot_div = fig.to_html(full_html=False)

#         context = {
#             "plot_div": plot_div,
#             "Job_Category": Job_Category,
#         }
#         print("success")
#         return render(request, "skills.html", context)


class SearchView(View):
    def get(self, request):
        skill = request.GET.get("skill")
        results = []

        if skill:
            entities = Entity.objects.filter(label="SKILL", text__icontains=skill)
            pdf_ids = entities.values_list("pdf_id", flat=True)
            pdfs = PDF.objects.filter(pk__in=pdf_ids)

            for pdf in pdfs:
                entity_data = Entity.objects.filter(pdf=pdf)
                skills = entity_data.filter(label="SKILL").values_list(
                    "text", flat=True
                )
                name = (
                    entity_data.filter(label="NAME")
                    .values_list("text", flat=True)
                    .first()
                )
                email = (
                    entity_data.filter(label="EMAIL")
                    .values_list("text", flat=True)
                    .first()
                )
                mobile = (
                    entity_data.filter(label="MOBILE")
                    .values_list("text", flat=True)
                    .first()
                )

                result = {
                    "pdf_name": pdf.name,
                    "skills": skills,
                    "name": name,
                    "email": email,
                    "mobile": mobile,
                }

                results.append(result)

        context = {"results": results, "skill": skill}
        return render(request, "search.html", context)


class LandingView(View):
    def get(self, request):
        return render(request, "landing.html")
