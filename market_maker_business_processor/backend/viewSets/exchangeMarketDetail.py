from rest_framework.viewsets import ModelViewSet
from ..models.exchangeMarketDetail import ExchangeMarketDetail
from ..serializers.exchangeMarketDetail import ExchangeMarketDetailSerializer

class ExchangeMarketDetailViewSet(ModelViewSet):
    queryset = ExchangeMarketDetail.objects.all()

    def get_serializer_class(self):
        return ExchangeMarketDetailSerializer
