from django.urls import path
from .views import PortfolioListView, PortfolioCardView, CreatePortfolioView, UpdatePortfolioNameView, \
    AddPacketToPortfolioView, DeletePacketView, GetPortfolioPredictionView

urlpatterns = [
    path('list', PortfolioListView.as_view(), name='portfolio-list'),
    path("portfolio-card/<int:pk>", PortfolioCardView.as_view(), name="portfolio-card"),
    path("create-portfolio", CreatePortfolioView.as_view(), name="create-portfolio"),
    path("portfolio-card/update/<int:pk>", UpdatePortfolioNameView.as_view(), name="update-portfolio"),
    path("portfolio-card/add-packet", AddPacketToPortfolioView.as_view(), name="add-packet"),
    path("portfolio-card/delete-packet", DeletePacketView.as_view(), name="delete-packet"),
    path("portfolio-card/<int:pk>/prediction", GetPortfolioPredictionView.as_view(), name="portfolio-prediction"),
]
