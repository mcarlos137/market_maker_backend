from django.db import models

class Status(models.IntegerChoices):
    active = 1
    inactive = 2

class HummingbotConnector(models.IntegerChoices):
    alt_markets = 1
    ascend_ex = 2
    ascend_ex_paper_trade = 3
    binance = 4
    binance_paper_trade = 5
    binance_us = 6
    bitfinex = 7
    bitmart = 8
    bittrex = 9
    bybit = 10
    bybit_testnet = 11
    ciex = 12
    coinbase_pro = 13
    coinstore = 34
    crypto_com = 14
    gate_io = 15
    gate_io_paper_trade = 16
    hitbtc = 17
    huobi = 18
    k2 = 19
    kraken = 20
    kucoin = 21
    kucoin_paper_trade = 22
    kucoin_testnet = 23
    lbank = 24
    loopring = 25
    mexc = 26
    mock_paper_exchange = 27
    ndax = 28
    ndax_testnet = 29
    okx = 30
    probit = 31
    probit_kr = 32
    tidex = 35
    whitebit = 33

class Exchange(models.Model):
    name = models.CharField(max_length=100)
    hummingbot_connector = models.IntegerField(choices=HummingbotConnector.choices, null=True)
    status = models.IntegerField(choices=Status.choices, default=Status.active)
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=True)
    
    def __str__(self):
        return "%s" % (self.name)
    
    class Meta:
        db_table = 'EXCHANGES'
