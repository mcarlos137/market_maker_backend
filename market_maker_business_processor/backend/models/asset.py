from django.db import models

class Type(models.IntegerChoices):
    base = 1
    quote = 2
    base_quote = 3

class Asset(models.Model):
    name = models.CharField(max_length=5, null=False)
    type = models.IntegerField(choices=Type.choices, default=Type.base, null=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=True)
    amount_decimals = models.SmallIntegerField(default=0, null=False)
    min_amount = models.DecimalField(max_digits=16, decimal_places=8, null=False)
    eth_token_contract_address = models.CharField(max_length=100)
    sol_token_contract_address = models.CharField(max_length=100)

    def __str__(self):
        return "%s-%s" % (self.name, self.type)

    class Meta:
        db_table = 'ASSETS'