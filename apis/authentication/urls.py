from django.urls import include, path
from rest_framework import routers

from apis.authentication.views import auth, user


router = routers.DefaultRouter()
router.register(r'user', user.UserViewSet, basename='user-auth')

api_v1_urls = (router.urls, "v1")


urlpatterns = [
    path("v1/", include(api_v1_urls)),
]
