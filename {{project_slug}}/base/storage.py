import re
from storages.backends.s3 import S3Storage

from django.core.exceptions import SuspiciousFileOperation
from django.core.files.base import ContentFile
from django.conf import settings


class MediaStorage(S3Storage):
    bucket_name = settings.S3_STORAGE_BUCKET_NAME

    def get_valid_name(self, name: str) -> str:
        s = str(name).strip().replace(" ", "_")
        s = re.sub(r"(?u)[^-\w.ก-๙]", "", s)
        if s in {"", ".", ".."}:
            raise SuspiciousFileOperation("Could not derive file name from '%s'" % name)
        return s

    def path(self, file_path):
        return file_path

    @staticmethod
    def get_filename(file_path):
        filename = str(file_path).split('/')
        return filename[-1]

    def get_file(self, path, filename):
        key = self.path(path)

        try:
            response_object = self.connection.meta.client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            file_bytes = response_object['Body'].read()
            return ContentFile(file_bytes, name=filename)

        except Exception as error:
            raise RuntimeError(f"Failed to get file from storage: {error}")

    def get_default_response_file(self, system_type):
        default_file_path = f'DEFAULT_DELIVER_FILES/{system_type}'
        _, files_in_path = self.listdir(default_file_path)

        default_files = []

        for file in files_in_path:
            file_path = f"{default_file_path}/{file}"
            default_files.append({
                "title": file,
                "path": file_path,
                "url": self.url(file_path),
                "type": self.open(file_path).obj.content_type,
            })

        return default_files


class StaticStorage(S3Storage):
    bucket_name = settings.S3_STATIC_BUCKET_NAME
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
    # querystring_auth = False


class TemporaryStorage(MediaStorage):
    bucket_name = settings.S3_TEMP_BUCKET_NAME


MEDIA_STORAGE = MediaStorage()

TEMP_STORAGE = TemporaryStorage()
