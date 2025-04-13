import datetime

from rest_framework import serializers

from .models import Currency, Fixing, CurrencyUSDFixing, Index


class GetCurrenciesListSerializer(serializers.ModelSerializer):
    currentUSDPrice = serializers.SerializerMethodField()
    monthlyDynamic = serializers.SerializerMethodField()

    class Meta:
        model = Currency
        fields = "__all__"

    def get_currentUSDPrice(self, instance):
        if instance.currency == "USD":
            return 1

        fixing = CurrencyUSDFixing.objects.filter(
            currencyId=instance,
        ).order_by("-currencyFixingDate").first()
        if fixing:
            return round(fixing.valueUSD, 2)
        return None

    def get_monthlyDynamic(self, instance):
        if instance.currency == "USD":
            return 0

        fixings = CurrencyUSDFixing.objects.filter(
            currencyId=instance,
        ).order_by("-currencyFixingDate")

        yesterday_fixing = fixings[0]
        last_month_fixing = fixings[30]

        if yesterday_fixing and last_month_fixing:
            return round(
                (yesterday_fixing.valueUSD / last_month_fixing.valueUSD - 1) * 100, 2
            )


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = "__all__"


class GetIndexesSerializer(serializers.ModelSerializer):
    currentPrice = serializers.SerializerMethodField()
    monthlyDynamic = serializers.SerializerMethodField()
    currency = CurrencySerializer(source="ccyId")

    class Meta:
        model = Index
        exclude = ["ccyId", ]
        # fields = "__all__"
        # depth = 1

    def get_currentPrice(self, instance):
        last_fixing = Fixing.objects.filter(indexId=instance).order_by("-fixingDate").first()

        if last_fixing:
            return f"{round(last_fixing.value, 2)}"

    def get_monthlyDynamic(self, instance):
        fixings = Fixing.objects.filter(
            indexId=instance,
        ).order_by("-fixingDate")

        try:
            yesterday_fixing = fixings[0]
            last_month_fixing = fixings[30]

            if yesterday_fixing and last_month_fixing:
                return round(
                    (yesterday_fixing.value / last_month_fixing.value - 1) * 100, 2
                )
        except Exception:
            return None
