from django.db import models
from .asset import Asset

class Status(models.IntegerChoices):
    active = 1
    inactive = 2

class MarketNew(models.Model):
    base_asset = models.ForeignKey(Asset, on_delete=models.PROTECT, null=False, related_name='base_asset')
    quote_asset = models.ForeignKey(Asset, on_delete=models.PROTECT, null=False, related_name='quote_asset')
    status = models.IntegerField(choices=Status.choices, default=Status.active)
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=True)
    price_decimals = models.SmallIntegerField(default=0, null=False)

    def symbol(self):
        return "%s-%s" % (self.base_asset.name, self.quote_asset.name)

    def __str__(self):
        return "%s-%s" % (self.base_asset.name, self.quote_asset.name)

    class Meta:
        db_table = 'MARKETS_NEW'