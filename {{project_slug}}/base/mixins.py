from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.decorators import action
from rest_framework.response import Response

from apis.general.models import AuditLog
from apis.general.serializers import AuditLogSerializer
from {{project_slug}}.base.paginations import CustomPageNumberPagination

from .functions import (
    XLSXExport, 
    CSVExport
)


class ExportMixin:
    """
    ExportMixin provides export functionality for ModelViewSet actions.
    This mixin adds two custom actions:
        - list_export: Exports a list of objects.
        - detail_export: Exports a single object.
    Both actions require a query parameter 'export_type' to specify the export format.
    Supported export formats are: 'csv', and 'xlsx'.
    Attributes:
        export_type_param (str): Name of the query parameter for export type.
        export_serializer_classes (dict): Serializer classes for list and detail export actions.
        export_class_map (dict): Maps export type strings to export handler classes.
        export_action_disable (list): List of export actions to disable (e.g., ["list_export", "detail_export"]).
    Methods:
        get_serializer_class(): Returns the appropriate serializer class for the export action.
        get_file_name(): Generates a filename for the exported file based on the current timestamp.
        _get_export_response(data, export_type): Returns a file response using the appropriate export class.
        list_export(request, *args, **kwargs): Action to export a list of objects.
        detail_export(request, *args, **kwargs): Action to export a single object.
        _check_export_action_disable(): Raises ValidationError if the current action is disabled.
    Raises:
        ValidationError: If an invalid export type is provided.
        NotFound: If the export action is disabled.
    """

    export_type_param = "export_type"
    export_serializer_classes = {
        "list_export": None,
        "detail_export": None,
    }
    export_class_map = {
        'csv': CSVExport,
        'xlsx': XLSXExport,
    }
    export_action_disable = []
    
    def get_export_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.export_serializer_classes.get(self.action, None) or self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_file_name(self):
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        return f"export_{timestamp}"

    def _check_export_action_disable(self):
        if self.action in self.export_action_disable:
            raise NotFound({"message": "This action is not found."})

    @action(methods=["GET"], detail=False, url_path="export")
    def list_export(self, request, *args, **kwargs):
        self._check_export_action_disable()
        limit_param = request.query_params.get('limit', None)
        page_param = request.query_params.get('page', None)
        export_type = request.query_params.get(self.export_type_param, None)

        if export_type not in self.export_class_map:
            raise ValidationError({"message": "Invalid export type. (csv, xlsx are supported)"})

        queryset = self.filter_queryset(self.get_queryset())
        if limit_param and page_param and self.paginator is not None:
            queryset = self.paginate_queryset(queryset)

        serializer = self.get_export_serializer(queryset, many=True)
        response = self._get_export_response(serializer.data, export_type)
        return response

    @action(methods=["GET"], detail=True, url_path="export")
    def detail_export(self, request, *args, **kwargs):
        self._check_export_action_disable()
        export_type = request.query_params.get(self.export_type_param, None)
        if export_type not in self.export_class_map:
            raise ValidationError({"message": "Invalid export type."})

        instance = self.get_object()
        serializer = self.get_export_serializer(instance)
        response = self._get_export_response(serializer.data, export_type)
        return response

    def _get_export_response(self, data, export_type):
        export_class = self.export_class_map[export_type]
        filename = self.get_file_name()
        response = export_class().response_file(data=data, filename=filename)
        return response


class AuditLogMixin:
    @action(
        methods=["GET"],
        detail=True,
        url_path="log",
        serializer_class=AuditLogSerializer,
        pagination_class=CustomPageNumberPagination,
    )
    def log_detail(self, request, *args, **kwargs):
        instance = self.get_object()
        ct = ContentType.objects.get_for_model(instance, for_concrete_model=False)
        audit_logs = AuditLog.objects.filter(
            object_type=ct, object_id=instance.pk
        ).order_by("-timestamp")

        page = self.paginate_queryset(audit_logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(audit_logs, many=True)
        return Response(serializer.data)
