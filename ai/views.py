from datetime import timedelta
from django.db.models import Count
from django.shortcuts import render
from rest_framework import generics
from django.utils.timezone import now
from rest_framework.views import APIView
from ai.models import ImageAnalysisResult
from rest_framework.response import Response
from .serializers import ImageAnalysisResultSerializer


# Create your views here.

class ImageAnalysisResultsListView(generics.ListAPIView):
    serializer_class = ImageAnalysisResultSerializer
    
    def get_queryset(self):
        queryset = ImageAnalysisResult.objects.filter(user=self.request.user).order_by("-id")
        
        limit = self.request.query_params.get('limit', "3")
        
        if limit == "all":
            return queryset
        
        try:
            limit = int(limit)
        except ValueError:
            limit = 3

        return queryset[:limit]
    
    
 
class AnalysisResultsDashboardView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        today = now().date()
        start_of_month = today.replace(day=1)
        
        # Analyses counts
        analyses_this_month = ImageAnalysisResult.objects.filter(
            user=user, created_at__date__gte=start_of_month
        ).count()

        last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
        analyses_last_month = ImageAnalysisResult.objects.filter(
            user=user,
            created_at__date__gte=last_month_start,
            created_at__date__lt=start_of_month
        ).count()

        # Improvement in count
        count_diff = analyses_this_month - analyses_last_month
        improvement = f"+{count_diff}" if count_diff >= 0 else str(count_diff)

        # Get latest two analyses
        latest_analyses = ImageAnalysisResult.objects.filter(user=user).order_by('-created_at')[:2]
        formatted = []

        for analysis in latest_analyses:
            serialized = ImageAnalysisResultSerializer(analysis).data
            avg_rating = None
            try:
                avg_rating = float(serialized.get("average_rating"))
            except (TypeError, ValueError):
                pass
            formatted.append({
                "average_rating": avg_rating,
                "ratings": serialized.get("ratings"),
                "ai_recommendations": serialized.get("ai_recommendations")
            })

        latest = formatted[0] if len(formatted) > 0 else None
        second_latest = formatted[1] if len(formatted) > 1 else None

        # Improvement in average score
        this_month_improvement_score = None
        if latest and second_latest and latest["average_rating"] is not None and second_latest["average_rating"] is not None:
            score_diff = round(latest["average_rating"] - second_latest["average_rating"], 2)
            this_month_improvement_score = f"+{score_diff}" if score_diff >= 0 else str(score_diff)

        # Symmetry improvement
        semmetric_improvement = None
        if latest and second_latest:
            try:
                sym_diff = round(latest["ratings"]["symmetry"] - second_latest["ratings"]["symmetry"], 2)
                semmetric_improvement = f"+{sym_diff}" if sym_diff >= 0 else str(sym_diff)
            except (TypeError, KeyError):
                semmetric_improvement = None

        return Response({
            "total_scans": analyses_this_month,
            "this_month_improvement": improvement,
            "latest_score": latest["average_rating"] if latest else None,
            "this_month_improvement_score": this_month_improvement_score,
            "symmetry": latest["ratings"].get("symmetry") if latest else None,
            "semmetric_improvement": semmetric_improvement,
            "ai_recommendations": latest.get("ai_recommendations") if latest else None,
        })