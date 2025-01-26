from django.db import models
from .telegramGroup import TelegramGroup
from .exchange import Exchange
from .exchangeNew import ExchangeNew
from django.db.models.signals import post_save

class Status(models.IntegerChoices):
    started = 1
    stopped = 2

class Type(models.IntegerChoices):
    price_change_percent = 1
    balance_out_of_limits = 2
    maker_orders_out_of_range = 3
    ask_ceiling_or_bid_floor_discover = 4
        
class Alert(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=True)
    status = models.IntegerField(choices=Status.choices, default=Status.stopped)    
    version = models.IntegerField(default=1, editable=False)
    type = models.IntegerField(choices=Type.choices)
    active_exchanges_new = models.ManyToManyField(ExchangeNew, blank=True)
    telegram_group = models.ForeignKey(TelegramGroup, on_delete=models.PROTECT, null=True)
    config = models.CharField(max_length=500)    
    message_output = models.CharField(max_length=1000)
          
    class Meta:
        db_table = 'ALERTS'
        ordering = ['-created_at']
        
    #@staticmethod
    #def post_save(sender, instance, created, **kwargs):   
    #    print('created', created)                     
    
    def __str__(self):
        return "ALERT: %s %s" % (self.name, self.type)
            
#post_save.connect(Alert.post_save, sender=Alert)
