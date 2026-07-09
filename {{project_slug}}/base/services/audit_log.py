from string import Formatter
from rest_framework.exceptions import ValidationError

from django.db import models

from apis.general.models import AuditLog, RelatedValueAuditLog


EXCLUDE_KEYS = {
    "created_at",
    "updated_at",
    "created_by",
    "updated_by",
    "url",
    "uuid"
}


class AuditLogService:

    @classmethod
    def log(cls, template_message, object, actor, tool, action, values_json: dict = {}, changes=None):
        """
        Create an audit log entry for tracking user actions in the system.

        This method records an activity performed by a user on a specific object.
        The log message can be dynamically generated using a template string
        with placeholders that will be replaced by values provided in `values_json`.

        Args:
            template_message (str):
                Message template describing the action. Supports placeholders
                using `{key}` syntax which will be replaced with values from
                `values_json`.

                Example:
                    "บันทึกการเก็บตัวอย่างดินและน้ำของ {sample__requester_name}"

            object (Model):
                Target object associated with this log entry.

            actor (User):
                The user who performed the action.

            tool (AuditLogTool):
                The system module where the action occurred
                (e.g. AuditLogTool.AUTH).

            action (AuditLogAction):
                The type of operation performed such as CREATE, UPDATE, or DELETE.

            values_json (dict, optional):
                Dictionary used to replace placeholders in `template_message`.

                Example:
                    {
                        "sample__requester_name": instance
                    }

            changes (dict, optional):
                Dictionary describing field changes between old and new values.
                Usually generated from `AuditLogService.create_diff_schema()`.

                Example:
                    {
                        "old": {
                            "name": "John",
                            "farmer_status": {
                                "label": "รออนุมัติแผนการตรวจประเมิน",
                                "value": 1
                            },
                        },
                        "new": {
                            "name": "Jane",
                            "farmer_status": {
                                "label": "ขอแก้ไขแผนการตรวจประเมิน",
                                "value": 2
                            },
                        },
                    }

        Example:
            Create log entry:

            AuditLogService.log(
                template_message="บันทึกการเก็บตัวอย่างดินและน้ำของ {sample__requester_name}",
                values_json={"sample__requester_name": instance},
                object=instance.inspection,
                actor=request.user,
                tool=AuditLogTool.INSPECTION,
                action=AuditLogAction.CREATE,
            )

            Update log entry with changes:

            changes = AuditLogService.create_diff_schema(old_data, new_data)

            AuditLogService.log(
                template_message="แก้ไขเจ้าหน้าที่ในคณะผู้ตรวจประเมิน",
                object=instance,
                actor=request.user,
                tool=AuditLogTool.INSPECTION,
                action=AuditLogAction.UPDATE,
                changes=changes,
            )
        """
        has_text_format = False
        default_value_related = ""
        # ----------------------- validate format string -----------------------
        list_text_format_check = []
        formatter = Formatter()
        for literal_text, text_format, format_spec, conversion in formatter.parse(template_message):
            if text_format is None:
                continue
            if text_format in list_text_format_check:
                raise ValidationError({"log": f"format string ห้ามซ้ำใน 'template_message'"})
            list_text_format_check.append(text_format)
            value_or_instance = values_json.get(text_format, None)
            if value_or_instance is None:
                raise ValidationError({"log": f"format string {text_format} ยังไม่ได้ระบุค่าใน 'values_json'"})
            if isinstance(value_or_instance, models.Model):
                validate_instance = value_or_instance
                list_attr = text_format.split("__")[1:]
                for attr in list_attr:
                    if hasattr(validate_instance, attr) == False:
                        raise ValidationError({"log": f"format string '{text_format}' ของ Model {value_or_instance.__class__.__name__} ไม่มี attribute {attr}"})
                    validate_instance = getattr(validate_instance, attr, None)
                default_value_related = getattr(value_or_instance, attr, "")
                has_text_format = True
            if isinstance(value_or_instance, models.Model) is False:
                template_message = template_message.replace(f"{{{text_format}}}", str(value_or_instance))
        # --------------------------------------------------------------------
        audit_log = AuditLog.objects.create(
            template_message=template_message,
            object=object,
            actor=actor,
            tool=tool,
            action=action,
            changes=changes,
        )
        if has_text_format:
            for _, text_format, _, _ in formatter.parse(template_message):
                if text_format is None:
                    continue
                obj = values_json.get(text_format, None)

                RelatedValueAuditLog.objects.create(
                    log=audit_log, text_format=text_format, object=obj, default_value=default_value_related
                )

    @classmethod
    def create_diff_schema(cls, old_data, new_data, exclude_keys=[]):
        exclude_keys = set(exclude_keys) | {
            "id",
            "created_at",
            "created_by",
            "updated_by",
            "updated_at",
            "uuid",
            "url",
        }

        def normalize_lists_to_dicts(data):
            """Convert list of dicts with id/uuid/document_type to dict keyed by it."""
            if isinstance(data, list):
                if all(isinstance(i, dict) for i in data):
                    keyed = {}
                    for item in data:
                        key = (
                            item.get("id")
                            or item.get("uuid")
                            or item.get("document_type")
                        )
                        if key is not None:
                            keyed[key] = normalize_lists_to_dicts(item)
                        else:
                            keyed[str(hash(str(item)))] = normalize_lists_to_dicts(item)
                    return keyed
                else:
                    return data[:]  # primitive list, keep as-is
            elif isinstance(data, dict):
                return {
                    k: normalize_lists_to_dicts(v)
                    for k, v in data.items()
                    if k not in exclude_keys
                }
            else:
                return data

        old_data = normalize_lists_to_dicts(old_data)
        new_data = normalize_lists_to_dicts(new_data)

        result = {"old_value": {}, "new_value": {}}

        def recursive_diff(old, new):
            """Recursive compare old/new, return (old_value, new_value)"""
            if isinstance(old, dict) and isinstance(new, dict):
                old_res, new_res = {}, {}
                all_keys = set(old.keys()) | set(new.keys())
                for k in all_keys:
                    o_val = old.get(k)
                    n_val = new.get(k)
                    ov, nv = recursive_diff(o_val, n_val)
                    if ov is not None or nv is not None:
                        old_res[k] = ov
                        new_res[k] = nv
                return old_res or None, new_res or None

            elif isinstance(old, list) and isinstance(new, list):
                # primitive list
                if not old or not isinstance(old[0], dict):
                    if old != new:
                        return old, new
                    return None, None
                # list of dict keyed by id
                old_map = (
                    {k: v for k, v in enumerate(old)} if isinstance(old, list) else old
                )
                new_map = (
                    {k: v for k, v in enumerate(new)} if isinstance(new, list) else new
                )

                all_keys = set(old_map.keys()) | set(new_map.keys())
                old_list_res = []
                new_list_res = []
                for k in all_keys:
                    o_val = old_map.get(k)
                    n_val = new_map.get(k)
                    ov, nv = recursive_diff(o_val, n_val)
                    if ov is not None or nv is not None:
                        old_list_res.append({k: ov})
                        new_list_res.append({k: nv})
                if old_list_res or new_list_res:
                    return old_list_res, new_list_res
                return None, None

            else:
                if old != new:
                    return old, new
                return None, None

        ov, nv = recursive_diff(old_data, new_data)
        result["old_value"] = ov or {}
        result["new_value"] = nv or {}
        return result
