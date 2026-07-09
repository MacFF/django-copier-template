from safedelete.models import SafeDeleteModel, SOFT_DELETE_CASCADE
from django.db import models
from django.conf import settings


class BaseModel(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE_CASCADE

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='created_by_%(class)s',
        on_delete=models.DO_NOTHING,
        blank=True, null=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='updated_by_%(class)s',
        on_delete=models.DO_NOTHING,
        blank=True, null=True,
    )

    class Meta:
        abstract = True
    
    @property
    def choices_information(self):
        return {
            'value': self.pk,
            'label': getattr(self, 'title', None)
        }


def get_system_user():
    from django.contrib.auth import get_user_model
    User = get_user_model() # NOSONAR
    return User.objects.get(email="system@mail.com")
