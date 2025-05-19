import datetime
from decimal import Decimal
from django.db import models


class Currency(models.Model):
    currency = models.CharField(verbose_name='ISO код валюты', max_length=50, default='RUB', unique=True)
    symbol = models.CharField(verbose_name='Символ валюты', max_length=10, default='₽', blank=True)
    ticker = models.CharField(verbose_name='Тикер вида {ISO}USD=X', max_length=50, blank=True)

    class Meta:
        verbose_name = "Валюта"
        verbose_name_plural = "Валюты"

    def __str__(self):
        return self.currency

    def get_price(self, request_currency=None, date=None):
        """Возвращает цену данной валюты в указанной валюте на дату"""
        if request_currency is None:
            request_currency = "USD"
        if date is None:
            date = datetime.date.today()

        # If converting to the same currency, return 1
        if self.currency == request_currency:
            return Decimal('1')

        # If converting from USD to another currency
        if self.currency == "USD":
            target_currency = Currency.objects.get(currency=request_currency)
            target_fixing = CurrencyUSDFixing.objects.filter(
                currencyId=target_currency,
                currencyFixingDate__lte=date
            ).order_by("-currencyFixingDate").first()
            
            if not target_fixing or not target_fixing.valueUSD:
                return Decimal('0.0')
            
            return Decimal('1') / target_fixing.valueUSD

        # If converting to USD or any other currency
        fixing = CurrencyUSDFixing.objects.filter(
            currencyId=self,
            currencyFixingDate__lte=date
        ).order_by("-currencyFixingDate").first()

        if not fixing:
            return Decimal('0.0')

        return fixing.get_value(request_currency)

    def get_dynamic(self, days=30, currency=None):
        """Возвращает относительное изменение стоимости за days дней в указанной валюте"""
        today = datetime.date.today()
        past = today - datetime.timedelta(days=days)
        current = self.get_price(request_currency=currency, date=today)
        previous = self.get_price(request_currency=currency, date=past)

        if previous == 0:
            return Decimal('0.0')

        return current / previous


class CurrencyUSDFixing(models.Model):
    currencyId = models.ForeignKey(Currency, blank=True, null=True, verbose_name="Валюта", on_delete=models.CASCADE)
    currencyFixingDate = models.DateField(blank=True, null=True, verbose_name="Дата валютного фиксинга")
    valueUSD = models.DecimalField(
        blank=True, null=True, max_digits=45, decimal_places=20, verbose_name="Стоимость в USD"
    )

    class Meta:
        verbose_name = "Фиксинг валюты в USD"
        verbose_name_plural = "Фиксинги валют в USD"

    def __str__(self):
        return f"{self.currencyId}_{self.currencyFixingDate}"

    def get_value(self, currency="USD"):
        if currency == "USD":
            return self.valueUSD

        target_fixing = CurrencyUSDFixing.objects.filter(
            currencyId__currency=currency,
            currencyFixingDate=self.currencyFixingDate
        ).first()

        if not target_fixing or not target_fixing.valueUSD:
            return Decimal('0.0')

        return self.valueUSD / target_fixing.valueUSD


class Index(models.Model):
    indexName = models.CharField(max_length=200, unique=True, blank=True, verbose_name="Имя актива")
    ccyId = models.ForeignKey(Currency, on_delete=models.SET_NULL, verbose_name="Код валюты", null=True)
    indexISIN = models.CharField(max_length=200, blank=True, verbose_name="ISIN идентификатора актива")

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"

    def __str__(self):
        return self.indexName

    def get_price(self, request_currency=None, date=None):
        """Возвращает цену бумаги в заданной валюте на указанную дату"""
        if request_currency is None:
            request_currency = self.ccyId.currency
        if date is None:
            date = datetime.date.today()

        fixing = Fixing.objects.filter(
            fixingDate__lte=date,
            indexId=self
        ).order_by("-fixingDate").first()

        if not fixing:
            return Decimal('0.0')

        return fixing.get_value(currency=request_currency)

    def get_dynamic(self, days=30, currency=None):
        """Возвращает изменение цены за указанный период в процентах"""
        today = datetime.date.today()
        past = today - datetime.timedelta(days=days)

        current = self.get_price(request_currency=currency, date=today)
        previous = self.get_price(request_currency=currency, date=past)

        if previous == 0:
            return None  # или Decimal('0.0') — в зависимости от желаемого поведения

        return ((current - previous) / previous) * 100


class Fixing(models.Model):
    fixingDate = models.DateField(blank=True, null=True, verbose_name="Дата фиксинга")
    indexId = models.ForeignKey(
        Index, blank=True, null=True, verbose_name="Идентификатор бумаги", on_delete=models.PROTECT
    )
    currencyId = models.ForeignKey(Currency, blank=True, null=True, verbose_name="Валюта", on_delete=models.PROTECT)
    value = models.DecimalField(blank=True, null=True, verbose_name="Цена закрытия", max_digits=45, decimal_places=20)

    class Meta:
        verbose_name = "Фиксинг"
        verbose_name_plural = "Фиксинги"

    def __str__(self):
        return f"{self.indexId}_{self.fixingDate}"

    def get_value(self, currency=None):
        if not self.value:
            return Decimal('0.0')

        if currency is None:
            return self.value

        if not self.currencyId:
            return Decimal('0.0')

        rate = Currency.objects.get(currency=currency).get_price(
            date=self.fixingDate,
            request_currency=self.currencyId.currency
        )

        if rate == 0:
            return Decimal('0.0')

        return self.value / rate
