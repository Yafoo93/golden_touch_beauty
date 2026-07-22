from core.models import BaseModel, BranchScopedModel


class POSSale(BaseModel, BranchScopedModel):
    """Branch-owned POS sale foundation; cashier and line items follow later."""

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"POS sale {self.pk} at {self.branch}"
