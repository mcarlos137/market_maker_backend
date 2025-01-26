from rest_framework.viewsets import ModelViewSet
from ..models.telegramGroup import TelegramGroup
from ..serializers.telegramGroup import TelegramGroupSerializer

class TelegramGroupViewSet(ModelViewSet):
    queryset = TelegramGroup.objects.all()

    def get_serializer_class(self):
        return TelegramGroupSerializer
