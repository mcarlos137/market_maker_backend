import json
from rest_framework import serializers
from .exchangeMarketDetail import ExchangeMarketDetailSerializer
from ..models.exchangeNew import ExchangeNew
from ..models.exchangeMarketDetail import ExchangeMarketDetail
from ..tools import attempt_json_deserialize

class ExchangeNewSerializer(serializers.ModelSerializer):
    markets_new = ExchangeMarketDetailSerializer(source="get_markets_new", many=True, required=False)
    
    class Meta:
        model = ExchangeNew
        #fields = ('id', 'name', 'status', 'size', 'type', 'created_at', 'buy_fee_percentage', 'buy_fee_asset_type', 'sell_fee_percentage', 'sell_fee_asset_type', 'markets')
        fields = ('id', 'name', 'status', 'size', 'type', 'created_at', 'buy_fee_percentage', 'buy_fee_asset_type', 'sell_fee_percentage', 'sell_fee_asset_type', 'markets', 'markets_new')
        read_only_fields = ('markets_new', 'name', 'created_at')
                    
    def create(self, validated_data):
        request = self.context['request']

        name = request.data.get('name')
        name = attempt_json_deserialize('name', name, expect_type=str)
        validated_data['name'] = name
                
        instance = super().create(validated_data)
        
        markets_new = request.data.getlist('markets_new')
        
        print('markets_new', markets_new)
        
        for market_new in markets_new:
            market_new = json.loads(market_new)
            market_new_id = market_new['id']
            buy_fee_percentage = None
            buy_fee_asset_type = None
            sell_fee_percentage = None
            sell_fee_asset_type = None
            collect = False
            preprocess = False
            
            if 'buy_fee_percentage' in market_new:
                buy_fee_percentage = market_new['buy_fee_percentage']
            if 'buy_fee_asset_type' in market_new:
                buy_fee_asset_type = market_new['buy_fee_asset_type']
            if 'sell_fee_percentage' in market_new:
                sell_fee_percentage = market_new['sell_fee_percentage']
            if 'sell_fee_asset_type' in market_new:
                sell_fee_asset_type = market_new['sell_fee_asset_type']
                
            if 'collect' in market_new:
                collect = market_new['collect']
            if 'preprocess' in market_new:
                preprocess = market_new['preprocess']
                
            exchange_market_detail = ExchangeMarketDetail.objects.create(
                exchange_id=instance.id,
                market_id=market_new_id,
                status=market_new['status'],
                use=market_new['use'],
                buy_fee_percentage=buy_fee_percentage,
                buy_fee_asset_type=buy_fee_asset_type,
                sell_fee_percentage=sell_fee_percentage,
                sell_fee_asset_type=sell_fee_asset_type,
                collect=collect,
                preprocess=preprocess
            )
            print('CREATE', exchange_market_detail)    
        
        return instance
    
    def update(self, instance, validated_data):
        request = self.context['request']    
        markets_new = request.data.getlist('markets_new')
        
        for market_new in markets_new:
            market_new = json.loads(market_new)
            market_new_id = market_new['id']
            buy_fee_percentage = None
            buy_fee_asset_type = None
            sell_fee_percentage = None
            sell_fee_asset_type = None
            collect = False
            preprocess = False
            
            if 'buy_fee_percentage' in market_new:
                buy_fee_percentage = market_new['buy_fee_percentage']
            if 'buy_fee_asset_type' in market_new:
                buy_fee_asset_type = market_new['buy_fee_asset_type']
            if 'sell_fee_percentage' in market_new:
                sell_fee_percentage = market_new['sell_fee_percentage']
            if 'sell_fee_asset_type' in market_new:
                sell_fee_asset_type = market_new['sell_fee_asset_type']
                            
            if 'collect' in market_new:
                collect = market_new['collect']
            if 'preprocess' in market_new:
                preprocess = market_new['preprocess']
                                
            exchanges_markets_details = ExchangeMarketDetail.objects.filter(exchange_id=instance.id, market_id=market_new_id)
            if len(exchanges_markets_details) > 0:
                exchange_market_detail = exchanges_markets_details[0]
                exchange_market_detail.status = market_new['status']
                exchange_market_detail.use = market_new['use']
                exchange_market_detail.buy_fee_percentage = buy_fee_percentage
                exchange_market_detail.buy_fee_asset_type = buy_fee_asset_type
                exchange_market_detail.sell_fee_percentage = sell_fee_percentage
                exchange_market_detail.sell_fee_asset_type = sell_fee_asset_type
                exchange_market_detail.collect = collect
                exchange_market_detail.preprocess = preprocess
                exchange_market_detail.save()
                print('UPDATE', exchange_market_detail)    
            else:
                exchange_market_detail = ExchangeMarketDetail.objects.create(
                    exchange_id=instance.id,
                    market_id=market_new_id,
                    status=market_new['status'],
                    use=market_new['use'],
                    buy_fee_percentage=buy_fee_percentage,
                    buy_fee_asset_type=buy_fee_asset_type,
                    sell_fee_percentage=sell_fee_percentage,
                    sell_fee_asset_type=sell_fee_asset_type,
                    collect=collect,
                    preprocess=preprocess
                )
                print('CREATE', exchange_market_detail)    
                
        instance = super().update(instance, validated_data)

        return instance
