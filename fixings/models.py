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


class Index(models.Model):
    indexName = models.CharField(max_length=200, unique=True, blank=True, verbose_name="Имя актива")
    ccyId = models.ForeignKey(Currency, on_delete=models.SET_NULL, verbose_name="Код валюты", null=True)
    indexISIN = models.CharField(max_length=200, blank=True, verbose_name="ISIN идентификатора актива")

    class Meta:
        verbose_name = "Акция"
        verbose_name_plural = "Акции"

    def __str__(self):
        return self.indexName


class Fixing(models.Model):
    fixingDate = models.DateField(blank=True, null=True, verbose_name="Дата фиксинга")
    indexId = models.ForeignKey(Index, blank=True, null=True, verbose_name="Идентификатор бумаги",
                                on_delete=models.PROTECT)
    currencyId = models.ForeignKey(Currency, blank=True, null=True, verbose_name="Валюта", on_delete=models.PROTECT)
    value = models.DecimalField(blank=True, null=True, verbose_name="Цена закрытия",
                                max_digits=45, decimal_places=20)

    class Meta:
        verbose_name = "Фиксинг"
        verbose_name_plural = "Фиксинги"

    def __str__(self):
        return f"{self.indexId}_{self.fixingDate}"


class CurrencyUSDFixing(models.Model):
    currencyId = models.ForeignKey(Currency, blank=True, null=True, verbose_name="Валюта", on_delete=models.CASCADE)
    currencyFixingDate = models.DateField(blank=True, null=True, verbose_name="Дата валютного фиксинга")
    valueUSD = models.DecimalField(blank=True, null=True, max_digits=45, decimal_places=20,
                                   verbose_name="Стоимость в USD")

    class Meta:
        verbose_name = "Фиксинг валюты в USD"
        verbose_name_plural = "Фиксинги валют в USD"

    def __str__(self):
        return f"{self.currencyId}_{self.currencyFixingDate}"
