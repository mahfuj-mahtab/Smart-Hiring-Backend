from rest_framework.exceptions import ValidationError

_REGISTRY: dict[tuple[str, str], type] = {}


def register_bulk_handler(resource: str, action: str, handler_cls):
    key = (resource, action)
    if key in _REGISTRY:
        raise ValueError(f"Bulk handler already registered for {resource}.{action}")
    _REGISTRY[key] = handler_cls


def get_bulk_handler(resource: str, action: str):
    handler_cls = _REGISTRY.get((resource, action))
    if handler_cls is None:
        raise ValidationError(
            {"action": f"Unknown bulk action '{action}' for resource '{resource}'."}
        )
    return handler_cls()
