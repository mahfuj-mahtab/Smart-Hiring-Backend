from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler

from apps.common.responses import api_response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        errors = response.data
        if isinstance(errors, dict) and "detail" in errors:
            message = str(errors["detail"])
            errors = {"detail": message}
        elif isinstance(errors, list):
            message = str(errors[0]) if errors else "Request failed"
            errors = {"detail": errors}
        else:
            message = "Validation failed" if response.status_code == 400 else "Request failed"

        return api_response(
            success=False,
            message=message,
            errors=errors,
            status=response.status_code,
        )

    return api_response(
        success=False,
        message="Internal server error",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
