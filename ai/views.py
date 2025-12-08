from statistics import mean
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
        
        
        
class ProgressView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        analyses = ImageAnalysisResult.objects.filter(user=user).order_by('created_at')
        rating = [analysis.ratings.skin_quality for analysis in analyses]
        user_created_at = user.created_at
        
        # Calculate this month and previous month date ranges
        today = now().date()
        start_of_this_month = today.replace(day=1)
        start_of_last_month = (start_of_this_month - timedelta(days=1)).replace(day=1)
        
        # Filter analyses for this month and last month
        analyses_this_month = [a for a in analyses if a.created_at.date() >= start_of_this_month]
        analyses_last_month = [a for a in analyses if start_of_last_month <= a.created_at.date() < start_of_this_month]
        
        # Calculate average ratings for this month
        ratings_this_month = [a.ratings.skin_quality for a in analyses_this_month]
        average_rating_this_month = round(sum(ratings_this_month) / len(ratings_this_month), 2) if ratings_this_month else 0
        
        # Calculate average ratings for last month
        ratings_last_month = [a.ratings.skin_quality for a in analyses_last_month]
        average_rating_last_month = round(sum(ratings_last_month) / len(ratings_last_month), 2) if ratings_last_month else 0
        
        # increse count of last month
        increse_goal_score = average_rating_this_month - average_rating_last_month
        
        data = {
            "days_active": (now().date() - user_created_at.date()).days,
            "since_at": user_created_at.strftime("%d %B"),
            "average_ratings": round(sum(rating) / len(analyses), 2) if analyses else 0,
            "increse_goal_score": increse_goal_score,
            "today_scans": len([analysis for analysis in analyses if analysis.created_at.date() == now().date()])
        }
        
        return Response(data)
    
    

class ScoreHistoryView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user

        # Get all analyses for the user
        analyses = ImageAnalysisResult.objects.filter(user=user).select_related('ratings')
        
        # Calculate average rating for each analysis and group into 0.5 ranges
        rating_counts = {}
        for analysis in analyses:
            ratings = [
                float(analysis.ratings.skin_quality or 0),
                float(analysis.ratings.jawline_definition or 0),
                float(analysis.ratings.cheekbone_structure or 0),
                float(analysis.ratings.eye_area or 0),
                float(analysis.ratings.facial_proportions or 0)
            ]
            avg_rating = sum(ratings) / 5
            
            # Group into 0.5 ranges (e.g., 6.0-6.5, 6.5-7.0)
            # Floor to nearest 0.5
            range_start = int(avg_rating * 2) / 2
            range_end = range_start + 0.5
            range_key = f"{range_start} to {range_end}"
            
            rating_counts[range_key] = rating_counts.get(range_key, 0) + 1
        
        # Sort by rating range and format output
        data = {
            "score_history": [
                {"rating": rating, "count": count}
                for rating, count in sorted(rating_counts.items(), key=lambda x: float(x[0].split(' ')[0]))
            ]
        }

        return Response(data)




class DetailedMetricsView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        analyses = ImageAnalysisResult.objects.filter(user=user).order_by('created_at')

        ratings_data = {
            "skin_quality": [a.ratings.skin_quality for a in analyses],
            "jawline_definition": [a.ratings.jawline_definition for a in analyses],
            "cheekbone_structure": [a.ratings.cheekbone_structure for a in analyses],
            "eye_area": [a.ratings.eye_area for a in analyses],
            "facial_proportions": [a.ratings.facial_proportions for a in analyses],
            "symmetry": [a.ratings.symmetry for a in analyses],
        }

        # average values
        average_data = {
            key: round(mean(value), 2) if value else 0
            for key, value in ratings_data.items()
        }

        data = {
            "detailed_metrics": average_data,
        }

        return Response(data)
