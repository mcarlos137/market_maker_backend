from rest_framework import serializers
from ..models.exchangeMarketDetail import ExchangeMarketDetail

class ExchangeMarketDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ExchangeMarketDetail
        fields = (
            'market', 
            'status', 
            'use', 
            'buy_fee_percentage', 
            'buy_fee_asset_type', 
            'sell_fee_percentage', 
            'sell_fee_asset_type', 
            'collect', 
            'preprocess'
            )
        