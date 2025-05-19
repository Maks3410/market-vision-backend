# portfolios/views.py
import datetime

from _decimal import Decimal
from rest_framework.generics import get_object_or_404, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from fixings.models import Index, Currency
from fixings.serializers import CurrencySerializer
from .models import Portfolio, IndexPacket
from .serializers import PortfolioListSerializer, PortfolioCardSerializer


class PortfolioListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        currency = request.query_params.get("currency", "USD")

        portfolios = Portfolio.objects.filter(userId=request.user).prefetch_related("packets__indexId")

        serializer = PortfolioListSerializer(
            portfolios,
            many=True,
            context={"currency": currency}
        )

        response = {"portfolios": serializer.data}

        currency_instance = Currency.objects.get(currency=currency)
        response["currency"] = CurrencySerializer(currency_instance).data
        return Response(response)


class PortfolioCardView(RetrieveAPIView):
    queryset = Portfolio.objects.prefetch_related("packets__indexId__ccyId")
    serializer_class = PortfolioCardSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["currency"] = self.request.query_params.get("currency", "USD")
        return context

    def delete(self, request, pk):
        portfolio = get_object_or_404(Portfolio, pk=pk, userId=request.user)
        portfolio.delete()
        return Response({"success": True})


class CreatePortfolioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get("name")
        if not name:
            name = f"Новый портфель от {datetime.date.today()}"
        portfolio = Portfolio.objects.create(userId=request.user, name=name)
        serializer = PortfolioCardSerializer(portfolio)
        return Response(serializer.data, status=201)


class UpdatePortfolioNameView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        portfolio = get_object_or_404(Portfolio, pk=pk, userId=request.user)
        name = request.data.get("name")
        if name:
            portfolio.name = name
            portfolio.save()
            return Response({"success": True, "name": portfolio.name})
        return Response({"error": "Name is required"}, status=400)


class AddPacketToPortfolioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        portfolio_id = request.data.get("portfolio_id")
        index_id = request.data.get("index_id")
        quantity = request.data.get("quantity")
        buy_date = request.data.get("buy_date")

        if not all([portfolio_id, index_id, quantity, buy_date]):
            return Response({"error": "Missing required fields"}, status=400)

        portfolio = get_object_or_404(Portfolio, id=portfolio_id, userId=request.user)
        index = get_object_or_404(Index, id=index_id)

        IndexPacket.objects.create(
            portfolioId=portfolio,
            indexId=index,
            quantity=int(quantity),
            buyDate=buy_date,
        )
        return Response({"success": True}, status=201)


class DeletePacketView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        packet_id = request.data.get("packet_id")
        if not packet_id:
            return Response({"error": "packet_id is required"}, status=400)

        packet = get_object_or_404(IndexPacket, id=packet_id, portfolioId__userId=request.user)
        packet.delete()
        return Response({"success": True})


class GetPortfolioPredictionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            # Получаем параметры из запроса
            currency = request.query_params.get("currency", "USD")
            days = int(request.query_params.get("days", 30))
            
            # Получаем портфель
            portfolio = get_object_or_404(Portfolio, pk=pk, userId=request.user)
            
            # Получаем текущую и прогнозируемую стоимость
            current_value = portfolio.get_current_value(currency=currency)
            predicted_value = portfolio.get_predicted_value(currency=currency, days=days)
            
            # Рассчитываем процент изменения
            if current_value == 0:
                growth_percent = Decimal('0.0')
            else:
                growth_percent = ((predicted_value - current_value) / current_value) * 100
            
            # Получаем информацию о валюте для отображения символа
            currency_instance = Currency.objects.get(currency=currency)
            
            return Response({
                "current_value": current_value,
                "predicted_value": predicted_value,
                "growth_percent": growth_percent,
                "currency": CurrencySerializer(currency_instance).data,
                "days": days
            })
            
        except ValueError:
            return Response(
                {"error": "Invalid days parameter"},
                status=400
            )
        except Currency.DoesNotExist:
            return Response(
                {"error": "Invalid currency"},
                status=400
            )
