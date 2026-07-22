import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


def migrate_assigned_managers(apps, schema_editor):
    Branch = apps.get_model("branches", "Branch")
    Assignment = apps.get_model("branches", "BranchStaffAssignment")
    for branch in Branch.objects.exclude(assigned_manager_id=None):
        Assignment.objects.get_or_create(
            branch_id=branch.id,
            staff_id=branch.assigned_manager_id,
            defaults={"roles": ["manager"], "permission_overrides": {}, "is_active": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("branches", "0002_branch_secondary_telephone_number_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BranchStaffAssignment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("roles", models.JSONField(default=list)),
                ("permission_overrides", models.JSONField(blank=True, default=dict)),
                ("is_active", models.BooleanField(default=True)),
                ("assigned_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_branch_staff_assignments", to=settings.AUTH_USER_MODEL)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="staff_assignments", to="branches.branch")),
                ("staff", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="branch_assignments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["branch__name", "staff__full_name"],
                "indexes": [
                    models.Index(fields=["branch", "is_active"], name="branch_staff_active_idx"),
                    models.Index(fields=["staff", "is_active"], name="staff_branch_active_idx"),
                ],
                "constraints": [models.UniqueConstraint(fields=("branch", "staff"), name="unique_staff_assignment_per_branch")],
            },
        ),
        migrations.RunPython(migrate_assigned_managers, migrations.RunPython.noop),
    ]
