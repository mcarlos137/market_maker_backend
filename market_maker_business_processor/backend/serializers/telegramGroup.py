from rest_framework import serializers
from ..models.telegramGroup import TelegramGroup
from ..tools import attempt_json_deserialize

class TelegramGroupSerializer(serializers.ModelSerializer):
        
    class Meta:
        model = TelegramGroup
        fields = (
            'id',
            'name', 
            'created_at', 
            'group_id', 
            'auth_token', 
        )
        read_only_fields = ['id', 'created_at']
                
    def create(self, validated_data):
        request = self.context['request']
        
        print('validated_data', validated_data)
        
        '''
        market = request.data.get('market')
        market = attempt_json_deserialize('market', market, expect_type=int)
        validated_data['market'] = market

        main_price_type = request.data.get('main_price_type')
        main_price_type = attempt_json_deserialize('main_price_type', main_price_type, expect_type=int)
        validated_data['main_price_type'] = main_price_type
        
        weighted_price_limit_time = request.data.get('weighted_price_limit_time')
        weighted_price_limit_time = attempt_json_deserialize('weighted_price_limit_time', weighted_price_limit_time, expect_type=int)
        validated_data['weighted_price_limit_time'] = weighted_price_limit_time
        
        weighted_price_max_tickers_per_source = request.data.get('weighted_price_max_tickers_per_source')
        weighted_price_max_tickers_per_source = attempt_json_deserialize('weighted_price_max_tickers_per_source', weighted_price_max_tickers_per_source, expect_type=int)
        validated_data['weighted_price_max_tickers_per_source'] = weighted_price_max_tickers_per_source
        
        weighted_price_exponential_factor = request.data.get('weighted_price_exponential_factor')
        weighted_price_exponential_factor = attempt_json_deserialize('weighted_price_exponential_factor', weighted_price_exponential_factor, expect_type=int)
        validated_data['weighted_price_exponential_factor'] = weighted_price_exponential_factor
        
        active_exchanges = request.data.get('active_exchanges')
        active_exchanges = attempt_json_deserialize('active_exchanges', active_exchanges, expect_type=list)
        validated_data['active_exchanges'] = active_exchanges
        
        price_floor = request.data.get('price_floor')
        price_floor = attempt_json_deserialize('price_floor', price_floor, expect_type=float)
        validated_data['price_floor'] = price_floor
        
        price_ceiling = request.data.get('price_ceiling')
        price_ceiling = attempt_json_deserialize('price_ceiling', price_ceiling, expect_type=float)
        validated_data['price_ceiling'] = price_ceiling
        '''
        instance = super().create(validated_data)

        return instance
    
    def update(self, instance, validated_data):
        request = self.context['request']

        print('validated_data', validated_data)

        '''
        if 'market' in validated_data:
            del validated_data['market']
            
        main_price_type = request.data.get('main_price_type')
        main_price_type = attempt_json_deserialize('main_price_type', main_price_type, expect_type=int)
        validated_data['main_price_type'] = main_price_type
        
        weighted_price_limit_time = request.data.get('weighted_price_limit_time')
        weighted_price_limit_time = attempt_json_deserialize('weighted_price_limit_time', weighted_price_limit_time, expect_type=int)
        validated_data['weighted_price_limit_time'] = weighted_price_limit_time
        
        weighted_price_max_tickers_per_source = request.data.get('weighted_price_max_tickers_per_source')
        weighted_price_max_tickers_per_source = attempt_json_deserialize('weighted_price_max_tickers_per_source', weighted_price_max_tickers_per_source, expect_type=int)
        validated_data['weighted_price_max_tickers_per_source'] = weighted_price_max_tickers_per_source
        
        weighted_price_exponential_factor = request.data.get('weighted_price_exponential_factor')
        weighted_price_exponential_factor = attempt_json_deserialize('weighted_price_exponential_factor', weighted_price_exponential_factor, expect_type=int)
        validated_data['weighted_price_exponential_factor'] = weighted_price_exponential_factor
        
        price_floor = request.data.get('price_floor')
        price_floor = attempt_json_deserialize('price_floor', price_floor, expect_type=float)
        validated_data['price_floor'] = price_floor
        
        price_ceiling = request.data.get('price_ceiling')
        price_ceiling = attempt_json_deserialize('price_ceiling', price_ceiling, expect_type=float)
        validated_data['price_ceiling'] = price_ceiling
        '''
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