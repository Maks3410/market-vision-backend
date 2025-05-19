"""
URL configuration for market_vision_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from .views import GetCurrenciesListView, GetIndexesListView, UpdateFixingsInfoView, GetAllCurrenciesListView, \
    GetAllIndexesListView

urlpatterns = [
    path('currencies/', GetCurrenciesListView.as_view()),
    path('indexes/', GetIndexesListView.as_view()),
    path('update-info', UpdateFixingsInfoView.as_view()),
    path('all-currencies-names', GetAllCurrenciesListView.as_view()),
    path('all-indexes', GetAllIndexesListView.as_view())
]
