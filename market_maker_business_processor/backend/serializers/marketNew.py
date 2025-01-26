from rest_framework import serializers
from ..models.marketNew import MarketNew
from ..models.asset import Asset
from ..tools import attempt_json_deserialize

class MarketNewSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = MarketNew
        fields = ('id', 'base_asset', 'quote_asset', 'status', 'created_at', 'price_decimals', 'symbol')
        
    def create(self, validated_data):
        request = self.context['request']
        
        base_asset = request.data.get('base_asset')
        base_asset = attempt_json_deserialize('base_asset', base_asset, expect_type=int)
        base_asset = Asset(id=base_asset)
        validated_data['base_asset'] = base_asset
        
        quote_asset = request.data.get('quote_asset')
        quote_asset = attempt_json_deserialize('quote_asset', quote_asset, expect_type=int)
        quote_asset = Asset(id=quote_asset)
        validated_data['quote_asset'] = quote_asset

        instance = super().create(validated_data)

        return instance
    
    def update(self, instance, validated_data):
        request = self.context['request']

        print('request------------', request.data)

        #market_data = request.data.get('market')
        #market_data = attempt_json_deserialize(market_data, expect_type=str)
        #validated_data['market'] = market_data

        instance = super().update(instance, validated_data)

        return instance
