from rest_framework import serializers
from ..models.market import Market
from ..tools import attempt_json_deserialize

class MarketSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Market
        fields = ('id', 'base', 'quote', 'status', 'created_at')
        
    def create(self, validated_data):
        request = self.context['request']

        base = request.data.get('base')
        base = attempt_json_deserialize('base', base, expect_type=str)
        validated_data['base'] = base
        
        quote = request.data.get('quote')
        quote = attempt_json_deserialize('quote', quote, expect_type=str)
        validated_data['quote'] = quote

        instance = super().create(validated_data)

        return instance
    
    '''
    def update(self, instance, validated_data):
        request = self.context['request']

        #market_data = request.data.get('market')
        #market_data = attempt_json_deserialize(market_data, expect_type=str)
        #validated_data['market'] = market_data

        instance = super().update(instance, validated_data)

        return instance
    '''