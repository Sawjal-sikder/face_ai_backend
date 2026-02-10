from rest_framework import generics, permissions, status #type: ignore
from rest_framework.response import Response #type:ignore
from .models import AnalysisCreditTransaction, PaypalEvent, Plan
from .serializers import PaypalEventSerializer, PlanSerializer, AnalysisCreditTransactionSerializer


class PlanViews(generics.ListCreateAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None
    
    
class PlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_url_kwarg = "id"
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Plan deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {
                "message": "Plan updated successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class PaypalEventViews(generics.ListCreateAPIView):
    queryset = PaypalEvent.objects.all()
    serializer_class = PaypalEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
        
class AnalysisCreditTransactionViews(generics.ListAPIView):
    queryset = AnalysisCreditTransaction.objects.all()
    serializer_class = AnalysisCreditTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None