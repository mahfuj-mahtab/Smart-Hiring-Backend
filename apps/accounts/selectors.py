from apps.accounts.models import OrganizationMember


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
