from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator

from apis.authentication.choices import UserStatus
from apis.authentication.tokens import CustomRefreshToken
from {{project_slug}}.base.serializers import BaseModelSerializer, ChoiceDisplayField, PasswordSerializerField, ThaiNationalIDField
from {{project_slug}}.base.services.export import ExportService


User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    token_class = CustomRefreshToken


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    token_class = CustomRefreshToken


USER_COLUMN_RENAME_MAP = {
    "permission": "ระดับการเข้าถึง",
    "full_name": "ชื่อ",
    "email": "อีเมล",
    "last_login": "ใช้งานล่าสุด",
    "status": "สถานะ"
}

class ExportUserListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True, default=None)
    last_login = serializers.DateTimeField(format="%d/%m/%Y", default="")
    status = serializers.ReadOnlyField(source="get_status_display")

    class Meta:
        model = User
        fields = ["permission", "full_name", "email", "last_login", "status"]
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return ExportService.rename_column_from_dict(data, USER_COLUMN_RENAME_MAP)


class ChangePasswordSerializer(BaseModelSerializer):
    password = PasswordSerializerField(required=True)

    def update(self, instance, validated_data):
        instance.set_password(validated_data['password'])
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ['password']


class ChangePasswordInfoSerializer(BaseModelSerializer):
    password = serializers.CharField(required=True)
    new_password = PasswordSerializerField(required=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if self.instance and not self.instance.check_password(attrs['password']):
            raise serializers.ValidationError({"password": _("รหัสผ่านเดิมไม่ถูกต้อง")})

        if attrs['password'] == attrs['new_password']:
            raise serializers.ValidationError({"new_password": _("รหัสผ่านใหม่ไม่สามารถเหมือนรหัสผ่านเดิมได้")})
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ['password', 'new_password']


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    status = ChoiceDisplayField(choices=UserStatus.choices, read_only=True)

    class Meta:
        model = User
        fields = ["id", "permission", "full_name", "email", "mobile_phone", "last_login", "status"]


class UserResponseSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    updated_by = serializers.StringRelatedField()

    class Meta:
        model = User
        exclude = (
            'password', 'is_superuser', 'is_staff', 'groups', 'deleted', 'deleted_by_cascade'
        )


class SetPasswordUserSerializer(serializers.ModelSerializer):
    password = PasswordSerializerField(
        required=True, allow_null=False, allow_blank=False
    )

    class Meta:
        model = User
        fields = ["password"]
    
    def update(self, user, validated_data):
        password = validated_data.pop("password")
        user.set_password(password)
        user.status = UserStatus.ACTIVE
        user.save()
        return user


class RegisterUserSerializer(BaseModelSerializer):
    email = serializers.EmailField(
        max_length=254,
        required=True,
        allow_null=False,
        allow_blank=False,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message=_("This email address is already in use."),
            )
        ],
    )
    password = PasswordSerializerField(required=True, allow_null=False, allow_blank=False)
    national_id = ThaiNationalIDField(
        required=False,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message=_("This national identification number has already been used.")
            )
        ]
    )
    mobile_phone = serializers.CharField(
        required=False,
        allow_null=False,
        allow_blank=False,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message=_("This mobile number is already in use."),
            )
        ],
    )

    class Meta:
        model = User
        read_only_fields = ['id']
        fields = [
            "id",
            "email",
            "username",
            "password",
            "prefix",
            "first_name",
            "last_name",
            "en_prefix",
            "en_first_name",
            "en_last_name",
            "national_id",
            "permission",
            "mobile_phone",
        ]
    
    def to_internal_value(self, data):
        email = data.get("email", "").strip().lower()
        data["username"] = email
        data["email"] = email
        return super().to_internal_value(data)
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        # user.set_unusable_password()
        user.save()
        return user
