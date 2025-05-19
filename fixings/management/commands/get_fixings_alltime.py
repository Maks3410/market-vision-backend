import datetime
from datetime import datetime, timedelta

import yfinance as yf
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError

from fixings.models import Currency, Index, Fixing, CurrencyUSDFixing


def download_ticker_data(ticker, start_date, end_date):
    """Download data for a single ticker with retries"""
    try:
        data = yf.download(
            tickers=ticker,
            start=start_date,
            end=end_date,
            interval="1d",
            progress=False
        )
        if not data.empty and 'Close' in data.columns:
            return data['Close'].dropna()
    except Exception as e:
        return None
    return None


def chunk_list(lst, chunk_size):
    """Split list into smaller chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


class Command(BaseCommand):
    help = "Загружает фиксинги валют и акций с 2020-01-01 до вчера."

    def handle(self, *args, **kwargs):
        try:
            # Initialize counters for reporting
            processed_tickers = 0
            failed_tickers = 0
            processed_fixings = 0
            processed_currency_fixings = 0
            failed_downloads = []

            start = datetime(2020, 1, 1).strftime("%Y-%m-%d")
            yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

            # Get all tickers
            currencies = list(Currency.objects.all().values_list('ticker', flat=True))
            index_list = list(Index.objects.all().values_list('indexISIN', flat=True))

            if not currencies and not index_list:
                self.stderr.write(self.style.WARNING("Нет данных о валютах и акциях в базе данных."))
                return

            tickers = currencies + index_list
            self.stdout.write(f"Начинаем загрузку данных для {len(tickers)} тикеров...")

            # Process tickers in smaller chunks and individually on failure
            closing_prices = {}
            chunk_size = 10  # Process 10 tickers at a time

            # First try batch download
            for chunk in chunk_list(tickers, chunk_size):
                try:
                    data = yf.download(
                        tickers=chunk,
                        start=start,
                        end=yesterday,
                        interval="1d",
                        group_by="ticker",
                        progress=False
                    )
                    
                    for ticker in chunk:
                        try:
                            if ticker in data.columns and ('Close' in data[ticker].columns):
                                prices = data[ticker]['Close'].dropna()
                                if not prices.empty:
                                    closing_prices[ticker] = prices
                                    processed_tickers += 1
                                    continue
                        except Exception:
                            pass
                        
                        # If batch download failed for this ticker, try individual download
                        prices = download_ticker_data(ticker, start, yesterday)
                        if prices is not None and not prices.empty:
                            closing_prices[ticker] = prices
                            processed_tickers += 1
                        else:
                            failed_downloads.append(ticker)
                            failed_tickers += 1
                            self.stdout.write(self.style.WARNING(f"Не удалось загрузить данные для {ticker}"))
                            
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Ошибка при загрузке пакета тикеров: {e}"))
                    # Try each ticker individually
                    for ticker in chunk:
                        prices = download_ticker_data(ticker, start, yesterday)
                        if prices is not None and not prices.empty:
                            closing_prices[ticker] = prices
                            processed_tickers += 1
                        else:
                            failed_downloads.append(ticker)
                            failed_tickers += 1
                            self.stdout.write(self.style.WARNING(f"Не удалось загрузить данные для {ticker}"))

            if not closing_prices:
                self.stderr.write(self.style.ERROR(
                    "Не удалось получить данные ни для одного тикера. "
                    "Существующие фиксинги останутся без изменений."
                ))
                return

            fixings = []
            currency_fixings = []

            # Prepare fixing objects
            for ticker, series in closing_prices.items():
                try:
                    if ticker in index_list:
                        index_id = Index.objects.filter(indexISIN=ticker).first()
                        if not index_id:
                            self.stdout.write(self.style.WARNING(f"Акция {ticker} не найдена в базе данных"))
                            continue
                        
                        ccy_id = index_id.ccyId
                        for date, close in series.items():
                            fixings.append(Fixing(
                                fixingDate=date,
                                indexId=index_id,
                                currencyId=ccy_id,
                                value=close
                            ))
                            processed_fixings += 1

                    elif ticker in currencies:
                        ccy_id = Currency.objects.filter(ticker=ticker).first()
                        if not ccy_id:
                            self.stdout.write(self.style.WARNING(f"Валюта {ticker} не найдена в базе данных"))
                            continue
                            
                        for date, close in series.items():
                            currency_fixings.append(CurrencyUSDFixing(
                                currencyFixingDate=date,
                                currencyId=ccy_id,
                                valueUSD=close
                            ))
                            processed_currency_fixings += 1

                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Ошибка при создании фиксингов для {ticker}: {e}"))

            if not fixings and not currency_fixings:
                self.stderr.write(self.style.ERROR(
                    "Не удалось создать ни одного фиксинга из полученных данных. "
                    "Существующие фиксинги останутся без изменений."
                ))
                return

            # Save to database within transaction
            try:
                with transaction.atomic():
                    self.stdout.write("Удаление старых фиксингов...")
                    if currency_fixings:
                        CurrencyUSDFixing.objects.all().delete()
                        self.stdout.write("Сохранение новых валютных фиксингов...")
                        CurrencyUSDFixing.objects.bulk_create(currency_fixings, batch_size=1000)
                    
                    if fixings:
                        Fixing.objects.all().delete()
                        self.stdout.write("Сохранение новых фиксингов акций...")
                        Fixing.objects.bulk_create(fixings, batch_size=1000)

            except IntegrityError as e:
                self.stderr.write(self.style.ERROR(f"Ошибка целостности данных при сохранении: {e}"))
                return
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Ошибка при сохранении данных: {e}"))
                return

            # Report success
            self.stdout.write(self.style.SUCCESS(
                f"Загрузка завершена успешно:\n"
                f"- Обработано тикеров: {processed_tickers} из {len(tickers)}\n"
                f"- Не удалось обработать тикеров: {failed_tickers}\n"
                f"- Создано фиксингов акций: {processed_fixings}\n"
                f"- Создано фиксингов валют: {processed_currency_fixings}\n"
                f"- Не удалось загрузить следующие тикеры:\n  {', '.join(failed_downloads)}"
            ))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Критическая ошибка: {e}"))
