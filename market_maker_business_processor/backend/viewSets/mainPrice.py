from rest_framework.viewsets import ModelViewSet
#from rest_framework.permissions import IsAdminUser
from ..models.mainPrice import MainPrice
from ..serializers.mainPrice import MainPriceSerializer

class MainPriceViewSet(ModelViewSet):
    queryset = MainPrice.objects.all()

    def get_serializer_class(self):
        return MainPriceSerializer
    
    '''
    permission_classes_by_action = {
        'create': [IsAdminUser],
        'list': [IsAdminUser],
        'retrieve': [IsAdminUser],
        'update': [IsAdminUser],
        'destroy': [IsAdminUser]
    }
    
    def get_permissions(self):
        try:
            # return permission_classes depending on `action` 
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError: 
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]
    '''