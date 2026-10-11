
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db.models import Q


class Command(BaseCommand):

    help = "Create Administrator and Farm Staff groups"

    def handle(self, *args, **options):

        administrator, _ = Group.objects.get_or_create(
            name="Administrator"
        )

        farm_staff, _ = Group.objects.get_or_create(
            name="Farm Staff"
        )

        administrator_permissions = Permission.objects.filter(
            content_type__app_label__in=[
                "production",
                "sales",
                "inventory",
                "accounting",
            ]
        )

        administrator.permissions.set(
            administrator_permissions
        )

        staff_permissions = Permission.objects.filter(
            content_type__app_label__in=[
                "production",
                "sales",
                "inventory",
            ]
        ).filter(
            Q(codename__startswith="view_")
            | Q(codename__startswith="add_")
        )

        farm_staff.permissions.set(
            staff_permissions
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Administrator and Farm Staff groups created."
            )
        )
