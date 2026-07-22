import re

from rest_framework import serializers

from accounts.models import User

from .models import Branch, BranchStaffAssignment


class PublicBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = (
            "id",
            "code",
            "name",
            "address",
            "telephone_number",
            "secondary_telephone_number",
            "whatsapp_number",
            "secondary_whatsapp_number",
            "email",
            "google_maps_url",
            "opening_days",
            "opening_time",
            "closing_time",
        )
        read_only_fields = fields


class ManagementBranchSerializer(serializers.ModelSerializer):
    assigned_manager = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = (
            "id", "code", "name", "address", "telephone_number",
            "secondary_telephone_number", "whatsapp_number",
            "secondary_whatsapp_number", "email", "google_maps_url",
            "opening_days", "opening_time", "closing_time",
            "assigned_manager", "is_active", "created_at", "updated_at",
        )
        read_only_fields = fields

    def get_assigned_manager(self, branch):
        manager = branch.assigned_manager
        if manager is None:
            return None
        return {"id": str(manager.id), "full_name": manager.full_name, "email": manager.email}


class ManagementBranchCreateSerializer(serializers.ModelSerializer):
    code = serializers.CharField(max_length=30)
    assigned_manager_id = serializers.PrimaryKeyRelatedField(
        source="assigned_manager",
        queryset=User.objects.filter(is_active=True, is_staff=True),
        required=False,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = Branch
        fields = (
            "id", "code", "name", "address", "telephone_number",
            "secondary_telephone_number", "whatsapp_number",
            "secondary_whatsapp_number", "email", "google_maps_url",
            "opening_days", "opening_time", "closing_time",
            "assigned_manager_id", "is_active",
        )
        read_only_fields = ("id",)

    def validate_code(self, value):
        code = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9_-]+", code):
            raise serializers.ValidationError(
                "Use letters, numbers, hyphens, or underscores only."
            )
        duplicate = Branch.objects.filter(code=code)
        if self.instance is not None:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError("A branch with this code already exists.")
        return code

    def validate_opening_days(self, value):
        valid_days = {
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        }
        if not value:
            raise serializers.ValidationError("Select at least one opening day.")
        normalized = list(dict.fromkeys(str(day).lower() for day in value))
        if any(day not in valid_days for day in normalized):
            raise serializers.ValidationError("One or more opening days are invalid.")
        return normalized

    def validate(self, attrs):
        opening_time = attrs.get("opening_time", getattr(self.instance, "opening_time", None))
        closing_time = attrs.get("closing_time", getattr(self.instance, "closing_time", None))
        if opening_time and closing_time and closing_time <= opening_time:
            raise serializers.ValidationError(
                {"closing_time": "Closing time must be later than opening time."}
            )
        return attrs

    def _activate_manager_assignment(self, branch, manager):
        if manager is None:
            return
        assignment, _ = BranchStaffAssignment.objects.get_or_create(
            branch=branch,
            staff=manager,
            defaults={
                "roles": [BranchStaffAssignment.Role.MANAGER],
                "assigned_by": self.context["request"].user,
            },
        )
        if BranchStaffAssignment.Role.MANAGER not in assignment.roles:
            assignment.roles.append(BranchStaffAssignment.Role.MANAGER)
        assignment.is_active = True
        assignment.assigned_by = self.context["request"].user
        assignment.save()

    def _remove_manager_role(self, branch, staff_id):
        if not staff_id:
            return
        try:
            assignment = BranchStaffAssignment.objects.get(branch=branch, staff_id=staff_id)
        except BranchStaffAssignment.DoesNotExist:
            return
        remaining_roles = [
            role for role in assignment.roles
            if role != BranchStaffAssignment.Role.MANAGER
        ]
        if remaining_roles:
            assignment.roles = remaining_roles
        else:
            assignment.is_active = False
        assignment.save()

    def create(self, validated_data):
        branch = super().create(validated_data)
        self._activate_manager_assignment(branch, branch.assigned_manager)
        return branch

    def update(self, instance, validated_data):
        manager_was_supplied = "assigned_manager" in validated_data
        previous_manager_id = instance.assigned_manager_id
        branch = super().update(instance, validated_data)
        if manager_was_supplied and previous_manager_id != branch.assigned_manager_id:
            self._remove_manager_role(branch, previous_manager_id)
            self._activate_manager_assignment(branch, branch.assigned_manager)
        return branch


class BranchManagerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "full_name", "email")
        read_only_fields = fields


class PickupItemSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField(required=False)
    sku = serializers.CharField(max_length=80, required=False)
    quantity = serializers.IntegerField(min_value=1, max_value=999)

    def validate(self, attrs):
        if bool(attrs.get("variant_id")) == bool(attrs.get("sku")):
            raise serializers.ValidationError(
                "Provide exactly one of variant_id or sku."
            )
        return attrs


class PickupOptionsRequestSerializer(serializers.Serializer):
    items = PickupItemSerializer(many=True, allow_empty=False)
