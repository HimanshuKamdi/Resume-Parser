"""
URL configuration for Hello project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "ResuMatic"
admin.site.site_title = "ResuMatic Portal"
admin.site.index_title = "We are glad to parse your resume!!"

urlpatterns = [
    path('admin/', admin.site.urls),     #it tells if anyone writes /admin then usko django admin pe bhej do
    path('', include('home.urls'))       #if this path i.e '' is matched then send it to home.urls
]
