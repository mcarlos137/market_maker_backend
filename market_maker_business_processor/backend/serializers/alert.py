from rest_framework import serializers
from ..models.alert import Alert
from ..tools import attempt_json_deserialize

class AlertSerializer(serializers.ModelSerializer):
                
    class Meta:
        model = Alert
        fields = (
            'id',
            'name', 
            'created_at', 
            'status', 
            'type', 
            'active_exchanges_new', 
            'telegram_group', 
            'config',
            'message_output'
        )
        read_only_fields = ['id', 'created_at']
                
    def create(self, validated_data):
        instance = super().create(validated_data)

        return instance
    
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        return instance

    def list(self, request):
        pass

    def retrieve(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass