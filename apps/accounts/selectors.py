from apps.accounts.models import OrganizationMember, User


def get_active_member(user, organization):
    if not user or not user.is_authenticated or organization is None:
        return None
    return (
        OrganizationMember.objects.select_related("role")
        .prefetch_related("role__permissions")
        .filter(user=user, organization=organization, is_active=True)
        .first()
    )


def user_has_permission(user, organization, codename):
    member = get_active_member(user, organization)
    if member is None:
        return False
    if member.is_owner:
        return True
    return member.role.permissions.filter(codename=codename).exists()


def get_user_permission_codenames(user, organization):
    member = get_active_member(user, organization)
    if member is None:
        return []
    if member.is_owner:
        from apps.accounts.models import Permission

        return list(Permission.objects.values_list("codename", flat=True))
    return list(member.role.permissions.values_list("codename", flat=True))


def lookup_employer_for_membership(*, organization, email):
    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        return {"status": "not_found"}
    if user.account_type == User.AccountType.CANDIDATE:
        return {"status": "invalid_account"}
    if OrganizationMember.objects.filter(organization=organization, user=user).exists():
        return {"status": "already_member"}
    return {
        "status": "found",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.get_full_name() or user.username,
        },
    }
