import datetime

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import generics, status, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .serializers import GetCurrenciesListSerializer, GetIndexesSerializer
from .models import Currency, Fixing, Index, CurrencyUSDFixing
import yfinance as yf


class LastUpdatePaginator(PageNumberPagination):
    page_size = 15

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        response.data["lastUpdate"] = Fixing.objects.latest('fixingDate').fixingDate
        response.data["pageSize"] = self.page_size
        return response


class GetCurrenciesListView(generics.ListAPIView):
    serializer_class = GetCurrenciesListSerializer
    queryset = Currency.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['currency', 'ticker', 'currentUSDPrice', 'monthlyDynamic']
    ordering = ['ticker']

    def filter_queryset(self, queryset):
        request = self.request
        ordering = request.query_params.get("ordering")
        reverse = False

        if ordering:
            if ordering.startswith("-"):
                reverse = True
                ordering = ordering[1:]

            if ordering in ["currentUSDPrice", "monthlyDynamic"]:
                queryset = list(queryset)

                def sort_key(obj):
                    serializer = self.get_serializer(obj)
                    return serializer.data.get(ordering)

                queryset.sort(key=sort_key, reverse=reverse)
                return queryset

        return super().filter_queryset(queryset)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        paginator = LastUpdatePaginator()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class GetIndexesListView(generics.ListAPIView):
    queryset = Index.objects.all()
    serializer_class = GetIndexesSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['indexName', 'indexISIN', 'currentPrice', 'currentUSDPrice', 'monthlyDynamic']
    ordering = ['indexISIN']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        paginator = LastUpdatePaginator()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def filter_queryset(self, queryset):
        request = self.request
        ordering = request.query_params.get("ordering")
        reverse = False

        if ordering:
            if ordering.startswith("-"):
                reverse = True
                ordering = ordering[1:]

            if ordering in ["currentPrice", 'currentUSDPrice', "monthlyDynamic"]:
                queryset = list(queryset)

                def sort_key(obj):
                    serializer = self.get_serializer(obj)
                    return serializer.data.get(ordering)

                queryset.sort(key=sort_key, reverse=reverse)
                return queryset

        return super().filter_queryset(queryset)


class UpdateFixingsInfoView(generics.RetrieveAPIView):

    def get(self, request, *args, **kwargs):
        start = (Fixing.objects.latest("fixingDate").fixingDate + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        if start > yesterday:
            return Response({"warning": "Данные уже обновлены"}, 200)

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
                Response({"error": f"Ошибка при обработке {ticker}: {e}"}, status=400)

        fixings = []
        currency_fixings = []
        count_success_indexes = 0
        count_success_currencies = 0

        for ticker, series in closing_prices.items():
            if ticker in index_list:
                index_id = Index.objects.filter(indexISIN=ticker).first()
                ccy_id = index_id.ccyId
                for date, close in series.items():
                    if not Fixing.objects.filter(fixingDate=date, indexId=index_id).exists():
                        fixings.append(Fixing(
                            fixingDate=date,
                            indexId=index_id,
                            currencyId=ccy_id,
                            value=close
                        ))
                        count_success_indexes += 1
            elif ticker in currencies:
                ccy_id = Currency.objects.filter(ticker=ticker).first()
                for date, close in series.items():
                    if not CurrencyUSDFixing.objects.filter(currencyFixingDate=date, currencyId=ccy_id).exists():
                        currency_fixings.append(CurrencyUSDFixing(
                            currencyFixingDate=date,
                            currencyId=ccy_id,
                            valueUSD=close
                        ))
                        count_success_currencies += 1

        CurrencyUSDFixing.objects.bulk_create(currency_fixings, batch_size=1000)
        Fixing.objects.bulk_create(fixings, batch_size=1000)

        if count_success_currencies + count_success_indexes == 0:
            return Response({"warning": "Последние фиксинги уже загружены"})

        return Response({
            "countCurrencies": count_success_currencies,
            "countIndexes": count_success_indexes,
            "startDate": start,
            "endDate": yesterday
        }, status=200)
