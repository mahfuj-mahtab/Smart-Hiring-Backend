from django.db import migrations

ORGANIZATION_ACTIONS = [
    ("view", "Can view"),
    ("add", "Can add"),
    ("change", "Can edit"),
    ("delete", "Can delete"),
]


def seed_organization_permissions(apps):
    Permission = apps.get_model("accounts", "Permission")
    for action, label_prefix in ORGANIZATION_ACTIONS:
        codename = f"organization.{action}"
        Permission.objects.get_or_create(
            codename=codename,
            defaults={
                "module": "organization",
                "action": action,
                "label": f"{label_prefix} organization",
            },
        )


def grant_organization_permissions_to_owner_roles(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")

    seed_organization_permissions(apps)

    org_permissions = Permission.objects.filter(module="organization")
    owner_roles = Role.objects.filter(name="Owner", is_system=True)
    for role in owner_roles:
        role.permissions.add(*org_permissions)


def revoke_organization_permissions_from_owner_roles(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")

    org_permissions = Permission.objects.filter(module="organization")
    owner_roles = Role.objects.filter(name="Owner", is_system=True)
    for role in owner_roles:
        role.permissions.remove(*org_permissions)


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0002_organization_profile_fields"),
        ("accounts", "0003_user_account_type_candidateprofile"),
    ]

    operations = [
        migrations.RunPython(
            grant_organization_permissions_to_owner_roles,
            revoke_organization_permissions_from_owner_roles,
        ),
    ]
