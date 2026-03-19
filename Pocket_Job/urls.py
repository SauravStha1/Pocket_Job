"""
URL configuration for Pocket_Job project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
"""
URL configuration for Pocket_Job project.
"""

from django.contrib import admin
from django.urls import path, include

# NEW IMPORTS
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),

    # Home page
    path('', include('homepage.urls')),
    path('jobs/', include('Job_Post.urls')),
    path('', include('accounts.urls')),
    path('chat/', include('chat.urls')),
]


# SERVE MEDIA FILES DURING DEVELOPMENT
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)