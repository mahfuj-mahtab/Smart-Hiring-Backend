from django.urls import path

from apps.organizations.viewsets import OrganizationViewSet, PublicOrganizationViewSet

organization_detail = OrganizationViewSet.as_view(
    {
        "get": "retrieve",
        "patch": "partial_update",
    }
)
public_organization_detail = PublicOrganizationViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("organization/", organization_detail, name="organization-detail"),
    path("public/organization/", public_organization_detail, name="public-organization-detail"),
]
