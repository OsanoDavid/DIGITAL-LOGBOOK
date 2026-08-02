"""URL configuration for sist_project project.

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
from django.urls import path, include
from django.conf import settings               # Added to read MEDIA variables
from django.conf.urls.static import static     # Added to serve file streams
from core import views # Imports views directly for the landing page hook

urlpatterns = [
    # /admin/ now redirects to the custom admin login page (portal/admins/)
    path('admin/', views.admin_login_view, name='custom_admin'),

    # Root-facing attachment admin aliases for direct console access
    path('admins/', views.admin_login_view, name='admin_login_root'),
    path('admins/dashboard/', views.admin_dashboard_view, name='admin_dashboard_root'),
    
    # 1. Maps the blank root URL directly to your landing login portal page
    path('', views.login_view, name='login'), 
    
    # 2. Includes all other workflow routes (register, dashboard, edit_log) from core/urls.py
    path('portal/', include(('core.urls', 'core'), namespace='core')),
]

# Append media file routing helper during local development environment checks
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)