import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from {{project_slug}}.base.storage import TEMP_STORAGE


class TemporaryFileView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        if file := request.data.get("file", None):
            if file.content_type not in settings.ALLOWED_FILE_TYPES:
                return Response(
                    {"message": "File type not support."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            file_path = f"{str(uuid.uuid4())}/{file.name}"
            key = TEMP_STORAGE.save(file_path, file)
            context = {
                "title": file.name,
                "path": file_path,
                "url": TEMP_STORAGE.url(key),
                "type": file.content_type,
            }
            return Response(context, status=status.HTTP_201_CREATED)

        return Response(
            {"message": "file is required."}, status=status.HTTP_400_BAD_REQUEST
        )
