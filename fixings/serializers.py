from rest_framework import serializers

from .models import Currency, Fixing, CurrencyUSDFixing, Index


class GetCurrenciesListSerializer(serializers.ModelSerializer):
    currentUSDPrice = serializers.SerializerMethodField()
    monthlyDynamic = serializers.SerializerMethodField()

    class Meta:
        model = Currency
        fields = "__all__"

    def get_currentUSDPrice(self, instance):
        return instance.get_price(request_currency="USD")

    def get_monthlyDynamic(self, instance):
        return (instance.get_dynamic(currency="USD") - 1) * 100


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
        return instance.get_price()

    def get_currentConvertedPrice(self, instance):
        return instance.get_price(request_currency=self.context.get("currency"))

    def get_monthlyDynamic(self, instance):
        return instance.get_dynamic()
