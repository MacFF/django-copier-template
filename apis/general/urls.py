from django.urls import include, path
from rest_framework import routers

from apis.general.views.audit_log import HistoryAuditLogViewSet


router = routers.DefaultRouter()
router.register(r"history-audit-logs", HistoryAuditLogViewSet)

api_v1_urls = (router.urls, "v1")

urlpatterns = [
    path("v1/", include(api_v1_urls)),
]
