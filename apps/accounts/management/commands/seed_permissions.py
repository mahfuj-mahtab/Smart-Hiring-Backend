from django.core.management.base import BaseCommand

from apps.accounts.models import Permission

MODULES = ["job", "candidate", "employee", "role"]
ACTIONS = [
    ("view", "Can view"),
    ("add", "Can add"),
    ("change", "Can edit"),
    ("delete", "Can delete"),
]


class Command(BaseCommand):
    help = "Seed global RBAC permission catalog"

    def handle(self, *args, **options):
        created_count = 0
        for module in MODULES:
            for action, label_prefix in ACTIONS:
                codename = f"{module}.{action}"
                _, created = Permission.objects.get_or_create(
                    codename=codename,
                    defaults={
                        "module": module,
                        "action": action,
                        "label": f"{label_prefix} {module}",
                    },
                )
                if created:
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Permissions seeded. Created {created_count} new permissions.")
        )
