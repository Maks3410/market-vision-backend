# portfolios/views.py
from _decimal import Decimal
from rest_framework.generics import get_object_or_404, RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from fixings.models import Index
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
        return Response(serializer.data)


class PortfolioCardView(RetrieveAPIView):
    queryset = Portfolio.objects.prefetch_related("packets__indexId__ccyId")
    serializer_class = PortfolioCardSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["currency"] = self.request.query_params.get("currency", "USD")
        return context


class CreatePortfolioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get("name")
        if not name:
            return Response({"error": "Name is required"}, status=400)
        portfolio = Portfolio.objects.create(userId=request.user, name=name)
        serializer = PortfolioCardSerializer(portfolio)
        return Response(serializer.data, status=201)


class UpdatePortfolioNameView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
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

        packet = get_object_or_404(IndexPacket, id=packet_id, portfolio__user=request.user)
        packet.delete()
        return Response({"success": True})


class DeletePortfolioView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
        portfolio.delete()
        return Response({"success": True})
