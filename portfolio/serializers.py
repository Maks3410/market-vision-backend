# portfolios/serializers.py

from rest_framework import serializers

from fixings.serializers import GetIndexesSerializer, CurrencySerializer
from .models import Portfolio, IndexPacket


class PortfolioListSerializer(serializers.ModelSerializer):
    currentValue = serializers.SerializerMethodField()
    dynamic = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ["id", "name", "currentValue", "dynamic"]

    def get_currentValue(self, obj):
        currency = self.context.get("currency", "USD")
        return obj.get_current_value(currency=currency)

    def get_dynamic(self, obj):
        currency = self.context.get("currency", "USD")
        return obj.get_dynamic_from_buy_date(currency=currency)


class IndexPacketDetailSerializer(serializers.ModelSerializer):
    index = GetIndexesSerializer(source="indexId")
    currency = serializers.SerializerMethodField()
    initialPrice = serializers.SerializerMethodField()
    currentPrice = serializers.SerializerMethodField()
    dynamicFromBuyDate = serializers.SerializerMethodField()
    initialConvertedPrice = serializers.SerializerMethodField()
    currentConvertedPrice = serializers.SerializerMethodField()
    convertedDynamicFromBuyDate = serializers.SerializerMethodField()

    class Meta:
        model = IndexPacket
        fields = [
            "id", "index", "currency", "buyDate", "quantity",
            "initialPrice", "currentPrice", "initialConvertedPrice", "currentConvertedPrice",
            "dynamicFromBuyDate", "convertedDynamicFromBuyDate",
        ]

    def get_currency(self, obj):
        return CurrencySerializer(obj.indexId.ccyId).data

    def get_initialPrice(self, obj):
        return obj.indexId.get_price(date=obj.buyDate)

    def get_currentPrice(self, obj):
        return obj.indexId.get_price()

    def get_dynamicFromBuyDate(self, obj):
        return obj.get_dynamic_from_buy_date()

    def get_initialConvertedPrice(self, obj):
        currency = self.context.get("currency", "USD")
        return obj.get_value(currency=currency, date=obj.buyDate)

    def get_currentConvertedPrice(self, obj):
        currency = self.context.get("currency", "USD")
        return obj.get_value(currency=currency)

    def get_convertedDynamicFromBuyDate(self, obj):
        currency = self.context.get("currency", "USD")
        return obj.get_dynamic_from_buy_date(currency=currency)


class PortfolioCardSerializer(serializers.ModelSerializer):
    currentValue = serializers.SerializerMethodField()
    packets = IndexPacketDetailSerializer(many=True, source="packets.all")
    dynamicFromBuyDate = serializers.SerializerMethodField()
    convertedDynamicFromBuyDate = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ["id", "name", "currentValue", "dynamicFromBuyDate", "convertedDynamicFromBuyDate", "packets"]

    def get_currentValue(self, obj):
        currency = self.context.get("currency", "USD")
        return obj.get_current_value(currency=currency)

    def get_dynamicFromBuyDate(self, obj):
        return obj.get_dynamic_from_buy_date()

    def get_convertedDynamicFromBuyDate(self, obj):
        currency = self.context.get("currency", "USD")
        return obj.get_dynamic_from_buy_date(currency=currency)
