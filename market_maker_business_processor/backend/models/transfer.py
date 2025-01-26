from django.db import models
from .exchange import Exchange
import json

class Currency(models.IntegerChoices):
    USDT = 1
    DAMEX = 2
    
class Type(models.IntegerChoices):
    deposit = 1
    withdraw = 2

class Transfer(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.PROTECT, db_column='exchange_id')
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=True)
    executed_at = models.DateTimeField(editable=False, null=False)
    currency = models.IntegerField(choices=Currency.choices)
    type = models.IntegerField(choices=Type.choices)
    amount = models.DecimalField(max_digits=16, decimal_places=8)
 
    def __json__(self):
        return json.dumps(self)
    
    class Meta:
        db_table = 'TRANSFERS'
