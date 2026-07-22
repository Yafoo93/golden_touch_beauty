from core.models import BaseModel, BranchScopedModel


class ReportSnapshot(BaseModel, BranchScopedModel):
    """Persisted branch report output; cross-branch reports aggregate snapshots."""

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report snapshot {self.pk} for {self.branch}"
