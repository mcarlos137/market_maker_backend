from rest_framework import serializers
from ..models.transfer import Transfer
from ..models.exchange import Exchange
from ..tools import attempt_json_deserialize

class TransferSerializer(serializers.ModelSerializer):
    
    executed_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    
    class Meta:
        model = Transfer
        fields = (
            'id',
            'exchange_id', 
            'created_at', 
            'executed_at',
            'currency', 
            'type', 
            'amount'
        )
        read_only_fields = ['id', 'created_at']
                        
    def create(self, validated_data):
        request = self.context['request']
        
        print('validated_data', validated_data)
        
        exchange_id = request.data.get('exchange_id')
        exchange_id = attempt_json_deserialize('exchange_id', exchange_id, expect_type=int)
        validated_data['exchange'] = Exchange.objects.get(id=exchange_id)
                
        currency = request.data.get('currency')
        currency = attempt_json_deserialize('currency', currency, expect_type=int)
        validated_data['currency'] = currency
        
        type = request.data.get('type')
        type = attempt_json_deserialize('type', type, expect_type=int)
        validated_data['type'] = type
        
        amount = request.data.get('amount')
        amount = attempt_json_deserialize('amount', amount, expect_type=float)
        validated_data['amount'] = amount
        
        instance = super().create(validated_data)
        
        return instance
    
    def update(self, instance, validated_data):
        pass        

    def list(self, request):
        pass

    def retrieve(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass