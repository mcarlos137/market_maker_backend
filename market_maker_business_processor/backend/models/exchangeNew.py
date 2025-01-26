from django.db import models
from .marketNew import MarketNew

class Status(models.IntegerChoices):
    active = 1
    inactive = 2
    
class Size(models.IntegerChoices):
    big = 1
    medium = 2
    small = 3

class Type(models.IntegerChoices):
    cex = 1
    dex = 2
    app = 3
        
class FeeAssetType(models.IntegerChoices):
    base = 1
    quote = 2

class ExchangeNew(models.Model):
    name = models.CharField(max_length=100)
    status = models.IntegerField(choices=Status.choices, default=Status.active)
    size = models.IntegerField(choices=Size.choices, default=Size.medium)
    type = models.IntegerField(choices=Type.choices, default=Type.cex)
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=True)
    buy_fee_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=False)
    buy_fee_asset_type = models.IntegerField(choices=FeeAssetType.choices, default=FeeAssetType.quote, null=False)
    sell_fee_percentage = models.DecimalField(max_digits=5, decimal_places=3, null=False)
    sell_fee_asset_type = models.IntegerField(choices=FeeAssetType.choices, default=FeeAssetType.quote, null=False)
    #markets = models.ManyToManyField(MarketNew, blank=True)
    markets = models.ManyToManyField(MarketNew, blank=True, through='ExchangeMarketDetail')
    
    def __str__(self):
        return "%s" % (self.name)
    
    def get_markets_new(self):
        return self.exchangemarketdetail_set.all()
    
    class Meta:
        db_table = 'EXCHANGES_NEW'

        