from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.tokens import default_token_generator

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.viewsets import mixins
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle, AnonRateThrottle

from apis.authentication.choices import UserStatus
from apis.authentication.serializers import (
    ChangePasswordInfoSerializer,
    ChangePasswordSerializer,
    ExportUserListSerializer,
    RegisterUserSerializer,
    SetPasswordUserSerializer,
    UserResponseSerializer,
    UserSerializer,
)
from {{project_slug}}.base.functions import decode_user_id, get_system_user
from {{project_slug}}.base.mixins import ExportMixin
from {{project_slug}}.base.services.email import EmailService
from {{project_slug}}.base.views import GenericActionViewSet


User = get_user_model()


class VerifyPasswordTokenAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def get(self, request, hashed_id, token):
        """เส้นสำหรับเช็คว่า Token หมดอายุหรือยัง (Verify Expire)"""
        try:
            uid = decode_user_id(hashed_id)
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, Exception):
            return Response({"message": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

        is_valid = default_token_generator.check_token(user, token)
        
        if is_valid:
            return Response(
                {"valid": True, "message": _("Token is usable.")},
                status=status.HTTP_200_OK,
            )
        
        return Response({
            "valid": False, 
            "message": _("Token is invalid or expired.")
        }, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        email = request.data.get("email", None)
        if email is None:
            return Response({"message": _("Email is required.")}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except (User.DoesNotExist, Exception):
            return Response({"message": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)
        
        EmailService.send_set_password_email(user=user)
        return Response({"message": _("A new set-password email has been sent.")}, status=status.HTTP_200_OK)


class SetPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "set_password"

    def post(self, request, hashed_id, token):
        uid = decode_user_id(hashed_id)
        user = get_object_or_404(User, pk=uid)

        if not default_token_generator.check_token(user, token):
            return Response({"message": _("Invalid or expired token.")}, status=status.HTTP_400_BAD_REQUEST)
        
        serialzier = SetPasswordUserSerializer(user, data=request.data, partial=True)
        serialzier.is_valid(raise_exception=True)
        serialzier.save()
        return Response({"message": _("Password set successfully.")}, status=status.HTTP_200_OK)


class UserViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  GenericActionViewSet,
                  ExportMixin):
    queryset = User.objects.none()
    serializer_class = UserResponseSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["permission"]
    search_fields = ["first_name", "last_name", "email"]

    export_serializer_classes = {
        "list_export": ExportUserListSerializer,
        "detail_export": None,
    }

    def get_queryset(self):
        return User.objects.exclude(pk=get_system_user().pk).exclude(is_superuser=True).order_by("-updated_at")
    
    def get_serializer_class(self):
        if self.action == "list":
            return UserSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request, *args, **kwargs):
        """
        Retrieve the current user's information.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @transaction.atomic
    @action(detail=False, methods=["post"], serializer_class=RegisterUserSerializer)
    def register(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_obj = serializer.save()
        EmailService.send_set_password_email(user=user_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    @transaction.atomic
    @action(detail=True, methods=["patch"])
    def suspend(self, request, *args, **kwargs):
        user_obj = self.get_object()

        if not user_obj.is_active and user_obj.status == UserStatus.SUSPENDED:
            return Response({"message": _("User is already suspended.")}, status=status.HTTP_400_BAD_REQUEST)
        
        user_obj.status = UserStatus.SUSPENDED
        user_obj.is_active = False
        user_obj.updated_by = request.user
        user_obj.save()
        return Response({"message": _("User was suspended.")}, status=status.HTTP_200_OK)


    @transaction.atomic
    @action(detail=True, methods=["patch"])
    def active(self, request, pk):
        user_obj = self.get_object()
        user_obj.status = UserStatus.ACTIVE
        user_obj.is_active = True
        user_obj.updated_by = request.user
        user_obj.save()
        return Response({"message": _("User was active.")}, status=status.HTTP_200_OK)


    @action(detail=True, methods=['patch'], url_path='change-password',
        permission_classes=[IsAuthenticated],
        serializer_class=ChangePasswordSerializer)
    def change_password(self, request, *args, **kwargs):
        """
        Change the current user's password.
        """
        user_obj = self.get_object()
        serializer = self.get_serializer(user_obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password changed successfully.'})
    

    @action(detail=False, methods=['post'], url_path='change-password-info',
        permission_classes=[IsAuthenticated],
        serializer_class=ChangePasswordInfoSerializer)
    def change_password_info(self, request, *args, **kwargs):
        """
        Change the current user's password.
        """
        serializer = self.get_serializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password changed successfully.'})


    @transaction.atomic
    @action(detail=True, methods=["patch"], url_path="resend-verification")
    def send_verification_email(self, request, pk):
        user_obj = self.get_object()

        if user_obj.status != UserStatus.PENDING:
            return Response({"message": _("Emails can only be sent to user status pending.")}, status=status.HTTP_400_BAD_REQUEST)
        
        EmailService.send_set_password_email(user=user_obj)
        return Response({"message": _("The email has been successfully sent.")}, status=status.HTTP_200_OK)
