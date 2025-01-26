from django.contrib import admin
from .models.market import Market
from .models.exchange import Exchange
from .models.mainPrice import MainPrice
from .models.transfer import Transfer
from .models.alert import Alert
from .models.telegramGroup import TelegramGroup

admin.site.register(Market)
admin.site.register(Exchange)
admin.site.register(Transfer)
admin.site.register(Alert)
admin.site.register(TelegramGroup)

class MainPriceAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'main_price_type']
    ordering = ['-created_at'] 
        
admin.site.register(MainPrice, MainPriceAdmin)
