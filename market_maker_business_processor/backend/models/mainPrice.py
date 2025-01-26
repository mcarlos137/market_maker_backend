from django.db import models
from .marketNew import MarketNew
from .exchangeNew import ExchangeNew


class MainPriceType(models.IntegerChoices):
    mid_price = 1
    last_price = 2
    last_own_trade_price = 3
    best_bid = 4
    best_ask = 5
    inventory_cost = 6
    weighted_price = 7
    
class MainPrice(models.Model):
    market_new = models.ForeignKey(MarketNew, on_delete=models.PROTECT, null=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=True)
    main_price_type = models.IntegerField(choices=MainPriceType.choices, default=MainPriceType.last_price)
    weighted_price_limit_time = models.IntegerField(default=300) #In seconds
    weighted_price_max_tickers_per_source = models.IntegerField(default=50)
    weighted_price_exponential_factor = models.IntegerField(default=1)
    active_exchanges_new = models.ManyToManyField(ExchangeNew, blank=True)
    price_floor = models.DecimalField(max_digits=16, decimal_places=6, default=0.01, null=False)
    price_ceiling = models.DecimalField(max_digits=16, decimal_places=6, default=1, null=False)

    @property
    def id(self):
        return self.id

    class Meta:
        db_table = 'MAIN_PRICES'