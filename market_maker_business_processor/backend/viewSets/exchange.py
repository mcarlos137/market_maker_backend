from rest_framework.viewsets import ModelViewSet
from ..models.exchange import Exchange
from ..serializers.exchange import ExchangeSerializer

class ExchangeViewSet(ModelViewSet):
    queryset = Exchange.objects.all()

    def get_serializer_class(self):
        return ExchangeSerializer
