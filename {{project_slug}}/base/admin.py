from django.contrib import admin
from django.db import models
from safedelete import HARD_DELETE


class BaseAdmin(admin.ModelAdmin):
    list_filter = ['created_at', 'updated_at']
    ordering = ['-id']

    def get_search_fields(self, request):
        return [
            field.name 
            for field in self.model._meta.fields
            if isinstance(field, models.CharField) or isinstance(field, models.TextField)
        ] + ['id']

    def get_list_display(self, request):
        list_display = [field.name for field in self.model._meta.fields]
        return list_display

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request, manager=None):
        return self.model.objects.order_by('-id')


class SafeDeleteBaseAdmin(BaseAdmin):
    list_filter = ['created_at', 'updated_at', 'deleted_by_cascade']
    actions = ['delete_by_cascade', 'undelete_by_cascade', 'hard_delete_by_cascade']

    @admin.action(description='Delete by cascade')
    def delete_by_cascade(self, request, queryset):
        queryset = queryset.filter(deleted__isnull=True)
        queryset.delete()

    @admin.action(description='Undelete by cascade')
    def undelete_by_cascade(self, request, queryset):
        queryset = queryset.filter(deleted__isnull=False)
        queryset.undelete()

    @admin.action(description='Hard delete by cascade')
    def hard_delete_by_cascade(self, request, queryset):
        queryset.delete(HARD_DELETE)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request, manager=None):
        return self.model.all_objects.order_by('-id')


class AutoUserAdminMixin:
    """Mixin to auto-fill created_by / updated_by from the logged-in user."""

    def get_exclude(self, request, obj=None):
        excluded = list(super().get_exclude(request, obj) or [])
        for field in ("created_by", "updated_by"):
            if field not in excluded:
                excluded.append(field)
        return excluded

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            is_new = obj.pk is None
            if is_new:
                obj.created_by = request.user
            obj.updated_by = request.user
            obj.save()
        # Handle deletions — formset.save(commit=False) does NOT delete automatically
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()
