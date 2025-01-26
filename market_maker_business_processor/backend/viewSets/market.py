from rest_framework.viewsets import ModelViewSet
from ..models.market import Market
from ..serializers.market import MarketSerializer

class MarketViewSet(ModelViewSet):
    queryset = Market.objects.all()

    def get_serializer_class(self):
        return MarketSerializer
