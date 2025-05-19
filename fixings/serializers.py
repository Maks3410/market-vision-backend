from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP

from .models import Currency, Fixing, CurrencyUSDFixing, Index


def round_decimal(value):
    """Rounds decimal to 4 places and removes trailing zeros"""
    if value is None:
        return Decimal('0')
    rounded = Decimal(str(value)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
    return rounded.normalize()


class GetCurrenciesListSerializer(serializers.ModelSerializer):
    currentConvertedPrice = serializers.SerializerMethodField()
    monthlyDynamic = serializers.SerializerMethodField()

    class Meta:
        model = Currency
        fields = "__all__"

    def get_currentConvertedPrice(self, instance):
        currency = self.context.get("currency", "USD")
        return round_decimal(instance.get_price(request_currency=currency))

    def get_monthlyDynamic(self, instance):
        currency = self.context.get("currency", "USD")
        return round_decimal((instance.get_dynamic(currency=currency) - 1) * 100)


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = "__all__"


class GetIndexesSerializer(serializers.ModelSerializer):
    currentPrice = serializers.SerializerMethodField()
    currentConvertedPrice = serializers.SerializerMethodField()
    monthlyDynamic = serializers.SerializerMethodField()
    currency = CurrencySerializer(source="ccyId")

    class Meta:
        model = Index
        exclude = ["ccyId", ]
        # fields = "__all__"
        # depth = 1

    def get_currentPrice(self, instance):
        return round_decimal(instance.get_price())

    def get_currentConvertedPrice(self, instance):
        return round_decimal(instance.get_price(request_currency=self.context.get("currency", "USD")))

    def get_monthlyDynamic(self, instance):
        return round_decimal(instance.get_dynamic())
