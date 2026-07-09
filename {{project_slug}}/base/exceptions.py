from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None and isinstance(response.data, dict):
        if "detail" in response.data:
            response.data["message"] = response.data.pop("detail")

    return response
