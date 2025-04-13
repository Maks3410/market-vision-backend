from django.contrib import admin

from .models import Currency, Index, Fixing, CurrencyUSDFixing


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ["currency", "symbol"]
    search_fields = ["currency",]


@admin.register(Index)
class IndexAdmin(admin.ModelAdmin):
    list_display = ["indexName", "ccyId__currency", "indexISIN"]
    search_fields = ["indexName", "indexISIN"]


@admin.register(Fixing)
class FixingAdmin(admin.ModelAdmin):
    list_display = ["indexId__indexName", "fixingDate", "value", "currencyId__symbol"]
    search_fields = ["indexId__indexName"]


@admin.register(CurrencyUSDFixing)
class CurrencyUSDFixingAdmin(admin.ModelAdmin):
    list_display = ["currencyId__currency", "currencyFixingDate", "valueUSD"]
    search_fields = ["currencyId__currency"]
