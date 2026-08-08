from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Receipt
from .serializers import ReceiptSerializer


def customer_receipts(user):
    return Receipt.objects.select_related("branch", "payment").filter(customer=user)


class CustomerReceiptListView(generics.ListAPIView):
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return customer_receipts(self.request.user)


class CustomerReceiptDetailView(generics.RetrieveAPIView):
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "reference"

    def get_queryset(self):
        return customer_receipts(self.request.user)
