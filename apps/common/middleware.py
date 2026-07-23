import logging

from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class SubdomainOrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.organization = None

        if self._is_exempt_path(request.path):
            return self.get_response(request)

        slug = self._resolve_slug(request)
        if slug is None:
            return self.get_response(request)

        from apps.organizations.models import Organization

        try:
            request.organization = Organization.objects.get(slug=slug, is_active=True)
        except Organization.DoesNotExist:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Organization not found",
                    "errors": {"organization": "Invalid or inactive organization subdomain."},
                },
                status=404,
            )

        return self.get_response(request)

    def _is_exempt_path(self, path):
        exempt_prefixes = getattr(
            settings,
            "ORGANIZATION_EXEMPT_PATHS",
            ["/admin/", "/api/v1/auth/"],
        )
        return any(path.startswith(prefix) for prefix in exempt_prefixes)

    def _resolve_slug(self, request):
        header_slug = request.headers.get(
            getattr(settings, "ORGANIZATION_HEADER_FALLBACK", "X-Organization-Slug")
        )
        if header_slug:
            return header_slug.strip().lower()

        host = request.get_host().split(":")[0].lower()
        base_domain = getattr(settings, "BASE_DOMAIN", "localhost").lower()

        if host == base_domain or host == "localhost" or host == "127.0.0.1":
            return None

        if host.endswith(f".{base_domain}"):
            subdomain = host[: -(len(base_domain) + 1)]
            if subdomain and subdomain not in getattr(settings, "RESERVED_SUBDOMAINS", []):
                return subdomain

        parts = host.split(".")
        if len(parts) >= 2 and parts[-1] in ("localhost", "local"):
            subdomain = parts[0]
            if subdomain not in getattr(settings, "RESERVED_SUBDOMAINS", []):
                return subdomain

        return None
