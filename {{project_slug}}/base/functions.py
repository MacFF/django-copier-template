import pandas as pd
from io import BytesIO
from typing import Optional
from hashids import Hashids

from django.http import HttpResponse
from django.conf import settings


def strtobool(value: str, nullable: bool = False) -> Optional[bool]:
    value = value.lower()
    if value in ("y", "yes", "on", "1", "true", "t"):
        return True
    elif value in ("n", "no", "off", "0", "false", "f"):
        return False
    else:
        return None if nullable else False

def strtolist(value: str) -> list[str]:
  return value.split(',') if value else []


class BaseExport:
    """
    content type and file extension reference: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/MIME_types/Common_types    
    """
    content_type = None
    file_extension = None

    def __init__(self, content_type: str=None, file_extension: str=None):
        self.content_type = content_type or self.content_type
        self.file_extension = file_extension or self.file_extension
        assert self.content_type, "content_type is required"
        assert self.file_extension, "file_extension is required"

    def make_file(self, data):
        raise NotImplementedError("Subclasses must implement make_file method")

    def response_file(self, data, filename: str = "export"):
        io_file = self.make_file(data)
        response = HttpResponse(
            io_file,
            content_type=self.content_type
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.{self.file_extension}"'

        return response

class XLSXExport(BaseExport):
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    file_extension = "xlsx"

    def make_file(self, data:dict):
        if isinstance(data, dict):
            data = [data]
        df = pd.DataFrame(data)
        with BytesIO() as output:
            df.to_excel(output, index=False, engine="openpyxl")
            return output.getvalue()


class CSVExport(BaseExport):
    content_type = "text/csv"
    file_extension = "csv"

    def make_file(self, data):
        if isinstance(data, dict):
            data = [data]
        df = pd.DataFrame(data)
        with BytesIO() as output:
            df.to_csv(output, index=False)
            return output.getvalue()

def get_system_user():
    from django.contrib.auth import get_user_model
    User = get_user_model() # NOSONAR
    return User.objects.get(email="system@mail.com")


def encode_user_id(user_id):
    hashids = Hashids(salt=settings.SECRET_KEY, min_length=12)
    return hashids.encode(user_id)


def decode_user_id(hashed_id):
    hashids = Hashids(salt=settings.SECRET_KEY, min_length=12)
    decoded = hashids.decode(hashed_id)
    return decoded[0] if decoded else None
