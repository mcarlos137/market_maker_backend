from rest_framework.viewsets import ModelViewSet
from ..models.exchangeNew import ExchangeNew
from ..serializers.exchangeNew import ExchangeNewSerializer

class ExchangeNewViewSet(ModelViewSet):
    queryset = ExchangeNew.objects.all()

    def get_serializer_class(self):
        return ExchangeNewSerializer
