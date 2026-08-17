import os
import re
from urllib.request import Request
from drf_writable_nested.serializers import WritableNestedModelSerializer

from django.db import transaction
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import SkipField

from {{project_slug}}.base.regx import RegexPatterns
from .storage import TEMP_STORAGE


User = get_user_model()

# ----------------------- Base Serializer Field -------------------------

class TitleRepresentSerializer(serializers.Serializer):
    def __init__(self, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_representation(self, instance):
        return {"id": instance.id, "title": instance.title}


class ChoiceDisplayField(serializers.ChoiceField):
    def to_representation(self, value):
        label = self.choices.get(value, value)
        if hasattr(label, "label"):
            label = label.label
        return {"value": value, "label": label}


class ModelValueLabelRepresentSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return {"value": instance.pk, "label": str(instance)}


class PasswordSerializerField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["write_only"] = True
        kwargs["required"] = True
        kwargs["min_length"] = 8
        super().__init__(*args, **kwargs)
        self.validators.append(
            RegexValidator(
                regex=RegexPatterns.PASSWORD["regex"],
                message=RegexPatterns.PASSWORD["message"],
            )
        )


class ThaiNationalDetailValidator:
    """
    Validator for Thai National ID.
    """
    error_messages = _("Invalid National ID.")
    code = "invalid"

    def get_sum_flag(self, value: str) -> str:
        total = sum(int(digit) * (13 - idx) for idx, digit in enumerate(value[:12]))
        check_digit = (11 - total % 11) % 10
        return str(check_digit)

    def __call__(self, value):
        value = str(value).replace("-", "").strip()
        person_type = value[0]
        sum_check = value[-1]
        if (not re.fullmatch(r'^\d{13}$', value) or
            not re.fullmatch(r'^\d$', person_type) or
            sum_check != self.get_sum_flag(value)
        ):
            raise serializers.ValidationError(self.error_messages, code=self.code)


class ThaiNationalIDField(serializers.CharField):
    """
    Custom field for validating Thai National ID.
    """
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 17
        kwargs['min_length'] = 13
        super().__init__(*args, **kwargs)
        self.validators.append(ThaiNationalDetailValidator())


class FileSerializerField(serializers.FileField):

    def to_internal_value(self, data):
        if hasattr(data, "read"):
            return super().to_internal_value(data)

        instance = getattr(self.parent, "instance", None)
        path = data.get("path")

        if instance:
            old_file = getattr(instance, self.field_name, None)
            if getattr(old_file, "name", None) == path:
                raise SkipField()

        return TEMP_STORAGE.get_file(data["path"], data["title"])


# ----------------------- Base Serializer Class -------------------------
 

class UserBaseSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name']

    @staticmethod
    def get_full_name(user: AbstractUser):
        return user.get_full_name()


class TitleRepresentSerializer(serializers.Serializer):
    def __init__(self, **kwargs):
        kwargs["read_only"] = True
        super().__init__(**kwargs)

    def to_representation(self, instance):
        return {"id": instance.id, "title": getattr(instance, "title")}


class BaseModelSerializer(WritableNestedModelSerializer):
    serializer_choice_field = ChoiceDisplayField
    created_by = serializers.HiddenField(default=serializers.CreateOnlyDefault(serializers.CurrentUserDefault()))
    updated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        abstract = True
        read_only_fields = ('created_at', 'updated_at')
        exclude = ['created_by', 'updated_by']

    def to_internal_value(self, data):
        self.request: Request = self.context.get('request', None)
        if self.request:
            self.context.update({
                'user': self.request.user
            })

        data = super().to_internal_value(data)

        if not self.instance:
            data.update({'created_by': self.context.get('user', None),
                         'updated_by': self.context.get('user', None)})
        else:
            data.update({'updated_by': self.context.get('user', None)})
        return data

    @transaction.atomic
    def create(self, validated_data):
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if 'deleted' in data and 'deleted_by_cascade' in data:
            data.pop('deleted')
            data.pop('deleted_by_cascade')

        meta = getattr(self, 'Meta', None)
        meta_fields = getattr(meta, 'fields', None)
        meta_exclude = getattr(meta, 'exclude', []) or []

        for field_name in ['created_by', 'updated_by']:
            should_show = (
                meta_fields == '__all__' or
                (isinstance(meta_fields, (list, tuple)) and field_name in meta_fields)
            ) and field_name not in meta_exclude

            if should_show:
                user = getattr(instance, field_name, None)
                data[field_name] = UserBaseSerializer(user).data if user else None

        return data


class BaseNestedCreateUpdateFileSerializer(BaseModelSerializer):
    title = serializers.CharField(required=True, write_only=True)
    path = serializers.CharField(required=True, write_only=True)
    url = serializers.CharField(required=False, write_only=True)
    type = serializers.CharField(required=True, allow_blank=True, write_only=True)
    file = serializers.FileField(read_only=True)

    def to_internal_value(self, data):
        if data.get("id") is None:
            data = super().to_internal_value(data)
            file = TEMP_STORAGE.get_file(data["path"], data["title"])

            if isinstance(file, Exception):
                raise serializers.ValidationError({"message": f"{file}"})

            data = {
                "file": file,
                "content_type": data["type"],
                "created_by": data["created_by"],
                "updated_by": data["updated_by"],
            }
        else:
            data = {}

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["path"] = str(getattr(instance, "file", None))
        data["url"] = data.pop("file", None)
        data["title"] = os.path.basename(data["path"])
        return data
