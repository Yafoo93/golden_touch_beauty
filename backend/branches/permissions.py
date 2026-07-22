from collections.abc import Iterable

from rest_framework.permissions import BasePermission

from .models import Branch, BranchStaffAssignment


MANAGEMENT_PORTAL_ROLES = {
    BranchStaffAssignment.Role.MANAGER,
    BranchStaffAssignment.Role.RECEPTIONIST,
    BranchStaffAssignment.Role.STOCK_MANAGER,
    BranchStaffAssignment.Role.SERVICE_PROVIDER,
}
POS_PORTAL_ROLES = {
    BranchStaffAssignment.Role.CASHIER,
    BranchStaffAssignment.Role.MANAGER,
}


def is_owner(user) -> bool:
    """Owners have global branch access, including inactive branches."""
    return bool(user and user.is_authenticated and user.is_active and user.is_superuser)


def _normalized_roles(roles: Iterable[str] | None) -> set[str]:
    return {str(role) for role in (roles or [])}


def get_accessible_branch_ids(user, required_roles: Iterable[str] | None = None) -> set:
    """Return active branches available through active staff assignments."""
    if not user or not user.is_authenticated or not user.is_active:
        return set()
    if is_owner(user):
        return set(Branch.objects.values_list("id", flat=True))

    required = _normalized_roles(required_roles)
    assignments = BranchStaffAssignment.objects.filter(
        staff=user,
        is_active=True,
        branch__is_active=True,
    ).values_list("branch_id", "roles", "permission_overrides")

    branch_ids = set()
    for branch_id, roles, overrides in assignments:
        if isinstance(overrides, dict) and overrides.get("can_access_branch") is False:
            continue
        if required and not required.intersection(roles or []):
            continue
        branch_ids.add(branch_id)
    return branch_ids


def can_access_branch(user, branch_or_id, required_roles: Iterable[str] | None = None) -> bool:
    if is_owner(user):
        return True
    branch_id = getattr(branch_or_id, "pk", branch_or_id)
    return branch_id in get_accessible_branch_ids(user, required_roles)


def get_staff_portal_access(user) -> list[str]:
    """Return portals authorized by active branch roles and explicit overrides."""
    if not user or not user.is_authenticated or not user.is_active:
        return []
    if is_owner(user):
        return ["management", "pos"]
    if not user.is_staff:
        return []

    access = set()
    assignments = BranchStaffAssignment.objects.filter(
        staff=user,
        is_active=True,
        branch__is_active=True,
    ).values_list("roles", "permission_overrides")
    for roles, overrides in assignments:
        normalized_roles = _normalized_roles(roles)
        normalized_overrides = overrides if isinstance(overrides, dict) else {}
        if normalized_overrides.get("can_access_branch") is False:
            continue
        if normalized_overrides.get("can_access_management") is True or (
            normalized_overrides.get("can_access_management") is not False
            and MANAGEMENT_PORTAL_ROLES.intersection(normalized_roles)
        ):
            access.add("management")
        if normalized_overrides.get("can_access_pos") is True or (
            normalized_overrides.get("can_access_pos") is not False
            and POS_PORTAL_ROLES.intersection(normalized_roles)
        ):
            access.add("pos")
    return [portal for portal in ("management", "pos") if portal in access]


def filter_queryset_by_branch_access(
    queryset,
    user,
    *,
    branch_lookup: str = "branch",
    required_roles: Iterable[str] | None = None,
):
    """Scope a queryset to the requesting user's permitted branches.

    Use ``branch_lookup=""`` when the queryset itself contains Branch records,
    or a Django relationship path such as ``order__branch`` for nested records.
    """
    if is_owner(user):
        return queryset
    branch_ids = get_accessible_branch_ids(user, required_roles)
    if not branch_ids:
        return queryset.none()
    lookup = "pk__in" if not branch_lookup else f"{branch_lookup}__pk__in"
    return queryset.filter(**{lookup: branch_ids})


class IsOwner(BasePermission):
    """Allow only the active owner/super-administrator account."""

    message = "Only the business owner can manage branches."

    def has_permission(self, request, view):
        return is_owner(request.user)


class IsOwnerOrAssignedBranchStaff(BasePermission):
    """Allow owners globally and staff only inside active branch assignments.

    Views may set ``required_branch_roles`` to a tuple of accepted assignment
    roles. Object checks support Branch objects and records with a ``branch``
    relationship. Create endpoints should submit ``branch`` or ``branch_id``.
    """

    message = "You are not assigned to this branch."

    def _required_roles(self, view):
        return getattr(view, "required_branch_roles", None)

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False
        if is_owner(user):
            return True

        branch_id = None
        if hasattr(request, "data"):
            branch_id = request.data.get("branch") or request.data.get("branch_id")
        branch_id = branch_id or view.kwargs.get("branch_pk") or view.kwargs.get("branch_id")
        if branch_id:
            return can_access_branch(user, branch_id, self._required_roles(view))
        return bool(get_accessible_branch_ids(user, self._required_roles(view)))

    def has_object_permission(self, request, view, obj):
        branch = obj if isinstance(obj, Branch) else getattr(obj, "branch", None)
        if branch is None:
            return False
        return can_access_branch(request.user, branch, self._required_roles(view))


class BranchAccessQuerysetMixin:
    """Apply branch assignment scoping to DRF view querysets."""

    branch_lookup = "branch"
    required_branch_roles = None

    def get_queryset(self):
        queryset = super().get_queryset()
        return filter_queryset_by_branch_access(
            queryset,
            self.request.user,
            branch_lookup=self.branch_lookup,
            required_roles=self.required_branch_roles,
        )
