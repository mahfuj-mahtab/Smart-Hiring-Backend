from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.auth_views import CandidateRegisterView, LoginView, RefreshTokenView, RegisterView
from apps.accounts.views import CandidateMeView, MeView, PermissionListView
from apps.accounts.viewsets import OrganizationMemberViewSet, RoleViewSet

router = DefaultRouter()
router.register("roles", RoleViewSet, basename="role")
router.register("members", OrganizationMemberViewSet, basename="member")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/register/candidate/", CandidateRegisterView.as_view(), name="auth-register-candidate"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="auth-refresh"),
    path("permissions/", PermissionListView.as_view(), name="permission-list"),
    path("me/", MeView.as_view(), name="me"),
    path("candidate/me/", CandidateMeView.as_view(), name="candidate-me"),
    path("", include(router.urls)),
]
