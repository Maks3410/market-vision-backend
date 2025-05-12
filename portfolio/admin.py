from django.contrib import admin
from portfolio.models import Portfolio, IndexPacket


class IndexPacketInline(admin.TabularInline):
    model = IndexPacket
    extra = 1
    fields = ("indexId", "quantity", "buyDate", "initialPrice")
    show_change_link = True


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ["userId", "name"]
    inlines = [IndexPacketInline]


@admin.register(IndexPacket)
class IndexPacketAdmin(admin.ModelAdmin):
    list_display = ["__str__", "get_portfolio_name", "indexId", "quantity", "buyDate", "get_initial_price"]

    def get_portfolio_name(self, obj):
        return obj.portfolioId.name
    get_portfolio_name.short_description = "Портфель акций"

    def get_initial_price(self, obj):
        return obj.get_initial_price()
    get_initial_price.short_description = "Начальная цена"
