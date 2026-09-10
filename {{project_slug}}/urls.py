"""
URL configuration for {{project_slug}} project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apis.authentication.views.auth import CustomLoginView
from apis.general.views.choice import ChoicesAPIView
from apis.general.views.temporary_file import TemporaryFileView


api_patterns = [
    path('v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('v1/auth/login/', CustomLoginView.as_view(), name='auth_login'),
    path('v1/choices/', ChoicesAPIView.as_view(), name='choices'),
    path('v1/temp-file/', TemporaryFileView.as_view(), name='temp-file'),

    path('', include(('apis.authentication.urls', 'apis.authentication'), namespace='user-authentication')),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
]
