from rest_framework.response import Response


def api_response(success, message, data=None, errors=None, status=200, pagination=None):
    body = {
        "success": success,
        "message": message,
    }
    if data is not None:
        body["data"] = data
    if errors is not None:
        body["errors"] = errors
    if pagination is not None:
        body["pagination"] = pagination
    return Response(body, status=status)
