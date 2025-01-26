from rest_framework.viewsets import ModelViewSet
from ..models.transfer import Transfer
from ..serializers.transfer import TransferSerializer

class TransferViewSet(ModelViewSet):
    queryset = Transfer.objects.all()

    def get_serializer_class(self):
        return TransferSerializer
