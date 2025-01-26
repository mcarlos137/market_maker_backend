from rest_framework import serializers
from ..models.exchange import Exchange
from ..tools import attempt_json_deserialize

class ExchangeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Exchange
        fields = ('id', 'name', 'hummingbot_connector', 'status', 'created_at')
                
    def create(self, validated_data):
        request = self.context['request']

        name = request.data.get('name')
        name = attempt_json_deserialize('name', name, expect_type=str)
        validated_data['name'] = name
        
        hummingbot_connector = request.data.get('hummingbot_connector')
        hummingbot_connector = attempt_json_deserialize('hummingbot_connector', hummingbot_connector, expect_type=int)
        validated_data['hummingbot_connector'] = hummingbot_connector

        instance = super().create(validated_data)

        return instance
    