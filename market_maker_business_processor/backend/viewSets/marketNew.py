from rest_framework.viewsets import ModelViewSet
from ..models.marketNew import MarketNew
from ..serializers.marketNew import MarketNewSerializer

class MarketNewViewSet(ModelViewSet):
    queryset = MarketNew.objects.all()

    def get_serializer_class(self):
        return MarketNewSerializer
