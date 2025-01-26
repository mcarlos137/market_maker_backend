from django.db import models
from .marketNew import MarketNew
from .exchangeNew import ExchangeNew

class Status(models.IntegerChoices):
    active = 1
    inactive = 2
        
class Use(models.IntegerChoices):
    mm = 1
    trading = 2
    mm_and_trading = 3
    
class FeeAssetType(models.IntegerChoices):
    base = 1
    quote = 2
        
class ExchangeMarketDetail(models.Model):
    exchange = models.ForeignKey(ExchangeNew, on_delete=models.PROTECT, null=True)
    market = models.ForeignKey(MarketNew, on_delete=models.PROTECT, null=True)
    status = models.IntegerField(choices=Status.choices, default=Status.active)
    use = models.IntegerField(choices=Use.choices, default=Use.mm_and_trading)
    buy_fee_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    buy_fee_asset_type = models.IntegerField(choices=FeeAssetType.choices, null=True)
    sell_fee_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    sell_fee_asset_type = models.IntegerField(choices=FeeAssetType.choices, null=True)
    collect = models.BooleanField(default=False)
    preprocess = models.BooleanField(default=False)
    
    def __str__(self):
        return "%s %s" % (self.exchange, self.market)
    
    class Meta:
        db_table = 'EXCHANGES_MARKETS_DETAILS'
        