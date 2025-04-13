import datetime

from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response

from .serializers import GetCurrenciesListSerializer, GetIndexesSerializer
from .models import Currency, Fixing, Index


class GetCurrenciesListView(generics.ListAPIView):
    serializer_class = GetCurrenciesListSerializer
    queryset = Currency.objects.all()

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class GetIndexesListView(generics.ListAPIView):
    queryset = Index.objects.all()
    serializer_class = GetIndexesSerializer

    def get_queryset(self):
        return self.queryset.order_by("indexName")

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
