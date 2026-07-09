from datetime import timedelta


SIMPLE_JWT = {
    'TOKEN_OBTAIN_SERIALIZER': 'apis.authentication.serializers.CustomTokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'apis.authentication.serializers.CustomTokenRefreshSerializer',
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'CHECK_REVOKE_TOKEN': True,
    'REVOKE_TOKEN_CLAIM': 'hash',
    'USER_ID_CLAIM': 'uid',
}
