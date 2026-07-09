def user_avatar_upload_path(instance, filename):
    return f"avatars/{instance.uuid}/{filename}"
