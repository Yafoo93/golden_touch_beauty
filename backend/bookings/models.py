from core.models import BaseModel, BranchScopedModel


class Booking(BaseModel, BranchScopedModel):
    """Branch-owned booking foundation; workflow fields are added in Stage 9."""

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking {self.pk} at {self.branch}"
