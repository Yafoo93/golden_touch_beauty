from core.models import BaseModel, BranchScopedModel


class Order(BaseModel, BranchScopedModel):
    """Branch-owned ecommerce order foundation; commerce fields follow later."""

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.pk} at {self.branch}"
