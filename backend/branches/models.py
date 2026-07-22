from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from core.models import BaseModel


class Branch(BaseModel):
    code_validator = RegexValidator(
        regex=r"^[A-Z0-9_-]+$",
        message="Use uppercase letters, numbers, hyphens, or underscores.",
    )

    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(
        max_length=30,
        unique=True,
        validators=[code_validator],
    )
    address = models.TextField()
    telephone_number = models.CharField(max_length=30)
    secondary_telephone_number = models.CharField(max_length=30, blank=True)
    whatsapp_number = models.CharField(max_length=30, blank=True)
    secondary_whatsapp_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    google_maps_url = models.URLField(blank=True)
    opening_days = models.JSONField(default=list)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    assigned_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="managed_branches",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "branches"

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


class BranchStaffAssignment(BaseModel):
    class Role(models.TextChoices):
        MANAGER = "manager", "Manager"
        RECEPTIONIST = "receptionist", "Receptionist"
        CASHIER = "cashier", "Cashier"
        STOCK_MANAGER = "stock_manager", "Stock manager"
        SERVICE_PROVIDER = "service_provider", "Service provider"

    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="staff_assignments",
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="branch_assignments",
    )
    roles = models.JSONField(default=list)
    permission_overrides = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_branch_staff_assignments",
    )

    class Meta:
        ordering = ["branch__name", "staff__full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "staff"],
                name="unique_staff_assignment_per_branch",
            )
        ]
        indexes = [
            models.Index(fields=["branch", "is_active"], name="branch_staff_active_idx"),
            models.Index(fields=["staff", "is_active"], name="staff_branch_active_idx"),
        ]

    def clean(self):
        super().clean()
        if self.staff_id and not (self.staff.is_staff or self.staff.is_superuser):
            raise ValidationError({"staff": "Only staff accounts can be assigned to a branch."})

        valid_roles = set(self.Role.values)
        if not isinstance(self.roles, list) or not self.roles:
            raise ValidationError({"roles": "Select at least one branch role."})
        if len(self.roles) != len(set(self.roles)):
            raise ValidationError({"roles": "Branch roles cannot be duplicated."})
        if any(role not in valid_roles for role in self.roles):
            raise ValidationError({"roles": "One or more branch roles are invalid."})
        if not isinstance(self.permission_overrides, dict):
            raise ValidationError({"permission_overrides": "Permission overrides must be an object."})

    def save(self, *args, **kwargs):
        self.roles = list(dict.fromkeys(self.roles)) if isinstance(self.roles, list) else self.roles
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.staff} at {self.branch}"
