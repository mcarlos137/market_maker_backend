"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
#from django.contrib import admin
from django.urls import path, include
#from django.contrib.auth.decorators import login_required
from rest_framework import routers
from .viewSets.market import MarketViewSet
from .viewSets.exchange import ExchangeViewSet

from .viewSets.asset import AssetViewSet
from .viewSets.marketNew import MarketNewViewSet
from .viewSets.exchangeNew import ExchangeNewViewSet

from .viewSets.exchangeMarketDetail import ExchangeMarketDetailViewSet

from .viewSets.mainPrice import MainPriceViewSet
from .viewSets.transfer import TransferViewSet
from .viewSets.user import UserViewSet
from .viewSets.alert import AlertViewSet
from .viewSets.telegramGroup import TelegramGroupViewSet
#from django_otp.admin import OTPAdminSite

#admin.site.__class__ = OTPAdminSite

router = routers.DefaultRouter()

## DEPRECATE
router.register(r"markets", MarketViewSet)
router.register(r"exchanges", ExchangeViewSet)
##

router.register(r"assets", AssetViewSet)
router.register(r"marketsNew", MarketNewViewSet)
router.register(r"exchangesNew", ExchangeNewViewSet)

router.register(r"exchangeMarketDetail", ExchangeMarketDetailViewSet)

router.register(r"mainPrices", MainPriceViewSet)
router.register(r"transfers", TransferViewSet)
router.register(r'users', UserViewSet)
router.register(r'alerts', AlertViewSet)
router.register(r'telegramGroups', TelegramGroupViewSet)

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('', include(router.urls)),
    #path('admin_tools_stats/', include('admin_tools_stats.urls')),
]