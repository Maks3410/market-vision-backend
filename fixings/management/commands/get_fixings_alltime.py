import datetime
from datetime import datetime, timedelta

import yfinance as yf
from django.core.management.base import BaseCommand

from fixings.models import Currency, Index, Fixing, CurrencyUSDFixing


def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)


class Command(BaseCommand):
    help = "Загружает фиксинги валют и акций с 2020-01-01 до вчера."

    def handle(self, *args, **kwargs):
        start = datetime(2020, 1, 1).strftime("%Y-%m-%d")
        yesterday = (datetime.today() - timedelta(days=10)).strftime("%Y-%m-%d")

        currencies = list(Currency.objects.all().values_list('ticker', flat=True))
        index_list = list(Index.objects.all().values_list('indexISIN', flat=True))

        tickers = currencies + index_list

        data = yf.download(
            tickers=tickers,
            start=start,
            end=yesterday,
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            threads=True,
        )

        closing_prices = {}

        for ticker in tickers:
            try:
                closing_prices[ticker] = data[ticker]['Close'].dropna()
            except Exception as e:
                print(f"Ошибка при обработке {ticker}: {e}")

        fixings = []
        currency_fixings = []

        for ticker, series in closing_prices.items():
            if ticker in index_list:
                index_id = Index.objects.filter(indexISIN=ticker).first()
                ccy_id = index_id.ccyId
                for date, close in series.items():
                    fixings.append(Fixing(
                        fixingDate=date,
                        indexId=index_id,
                        currencyId=ccy_id,
                        value=close
                    ))
            elif ticker in currencies:
                ccy_id = Currency.objects.filter(ticker=ticker).first()
                for date, close in series.items():
                    currency_fixings.append(CurrencyUSDFixing(
                        currencyFixingDate=date,
                        currencyId=ccy_id,
                        valueUSD=close
                    ))

        Fixing.objects.all().delete()
        CurrencyUSDFixing.objects.all().delete()

        CurrencyUSDFixing.objects.bulk_create(currency_fixings, batch_size=1000)
        Fixing.objects.bulk_create(fixings, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f""))
