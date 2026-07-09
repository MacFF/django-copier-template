from uuid import uuid4

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apis.authentication.models import FamilyRefreshToken


class CustomRefreshToken(RefreshToken):

    @classmethod
    def for_user(cls, user):
        """
        This function create and return Refresh Token
        Adds this token to the outstanding token list and Create FamilyRefreshToken.
        """
        refresh_token = super().for_user(user)
        family_uuid = uuid4().hex
        refresh_token["fam"] = family_uuid
        FamilyRefreshToken.objects.create(family=family_uuid)
        return refresh_token
    
    
    def check_blacklist(self) -> None:
        """
        Checks if this token is present in the token blacklist.  Raises
        `Token is blacklisted` and update FamilyRefreshToken to blacklist.

        if familty refresh token is blacklist. Raises
        `Token reuse detected. Family revoked.`
        """
        jti = self.payload[api_settings.JTI_CLAIM]
        fam_uuid = self.payload["fam"]

        if FamilyRefreshToken.objects.filter(family=fam_uuid, is_blacklisted=True).exists():
            raise TokenError(_("Token reuse detected. Family revoked."))

        if BlacklistedToken.objects.filter(token__jti=jti).exists():
            FamilyRefreshToken.objects.filter(family=fam_uuid).update(is_blacklisted=True, blacklisted_at=timezone.now())
            raise TokenError(_("Token is blacklisted"))
