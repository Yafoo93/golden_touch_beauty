from core.models import BaseModel, BranchScopedModel


class Payment(BaseModel, BranchScopedModel):
    """Branch-owned payment foundation; gateway and allocation fields follow."""

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.pk} at {self.branch}"


class Receipt(BaseModel, BranchScopedModel):
    """A receipt always retains the branch that issued it."""

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Receipt {self.pk} from {self.branch}"
