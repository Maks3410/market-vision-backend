import datetime

from _decimal import Decimal
from django.db import models

from authentication.models import User
from fixings.models import Index


class Portfolio(models.Model):
    userId = models.ForeignKey(User, verbose_name="Владелец портфеля", on_delete=models.PROTECT)
    name = models.CharField(max_length=255, verbose_name="Название портфеля")

    class Meta:
        verbose_name = "Портфель акций"
        verbose_name_plural = "Портфели акций"

    def __str__(self):
        return f"{self.name} ({self.userId.username})"

    def get_initial_value(self, currency=None):
        return sum(
            packet.get_initial_value(currency)
            for packet in self.packets.select_related('indexId__ccyId').all()
        )

    def get_current_value(self, currency=None):
        return sum(
            packet.get_value(currency=currency)
            for packet in self.packets.select_related('indexId__ccyId').all()
        )

    def get_value(self, currency="USD", date=None):
        if date is None:
            date = datetime.date.today()

        return sum(
            packet.get_value(currency=currency, date=date)
            for packet in self.packets.select_related('indexId__ccyId').all()
        )

    def get_dynamic_from_buy_date(self, currency=None):
        initial = self.get_initial_value(currency=currency)
        current = self.get_current_value(currency=currency)

        if initial == 0:
            return Decimal('0.0')

        return ((current - initial) / initial) * 100


class IndexPacket(models.Model):
    portfolioId = models.ForeignKey(Portfolio, related_name="packets", on_delete=models.CASCADE)
    indexId = models.ForeignKey(Index, verbose_name="Акция", on_delete=models.PROTECT)
    quantity = models.IntegerField(verbose_name="Количество акции")
    buyDate = models.DateField(verbose_name="Дата покупки")

    class Meta:
        verbose_name = "Пакет акции"
        verbose_name_plural = "Пакеты акций"

    def __str__(self):
        return f"{self.quantity}_{self.indexId}_{self.buyDate}"

    def get_value(self, currency=None, date=None):
        if currency is None:
            currency = self.indexId.ccyId.currency
        if date is None:
            date = datetime.date.today()

        return self.quantity * self.indexId.get_price(request_currency=currency, date=date)

    def get_dynamic(self, days=30, currency=None):
        return self.indexId.get_dynamic(days=days, currency=currency)

    def get_initial_value(self, currency):
        return self.get_value(currency=currency, date=self.buyDate)

    def get_dynamic_from_buy_date(self, currency=None):
        initial = self.get_value(currency=currency, date=self.buyDate)
        current = self.get_value(currency=currency)

        if initial == 0:
            return Decimal('0.0')

        return ((current - initial) / initial) * 100
