from rest_framework import serializers
from ..models.mainPrice import MainPrice
from ..tools import attempt_json_deserialize

class MainPriceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = MainPrice
        fields = (
            'id',
            'market_new',
            'created_at', 
            'main_price_type', 
            'weighted_price_limit_time', 
            'weighted_price_max_tickers_per_source',
            'weighted_price_exponential_factor',
            'active_exchanges_new',
            'price_floor',
            'price_ceiling'
        )
        read_only_fields = ['id', 'created_at']
                
    def create(self, validated_data):
        request = self.context['request']
        
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
                
        active_exchanges_new = request.data.get('active_exchanges_new')
        active_exchanges_new = attempt_json_deserialize('active_exchanges_new', active_exchanges_new, expect_type=list)
        validated_data['active_exchanges_new'] = active_exchanges_new
                
        instance = super().create(validated_data)

        return instance
    
    def update(self, instance, validated_data):
        request = self.context['request']
            
        if 'market_new' in validated_data:
            del validated_data['market_new']
            
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