import datetime
from statistics import mean
from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from rest_framework import generics
from django.utils.timezone import now
from django.db.models import Count, Sum
from rest_framework.views import APIView
from ai.models import ImageAnalysisResult
from rest_framework.response import Response
from .serializers import ImageAnalysisResultSerializer
from django.contrib.auth import get_user_model
from payment.models import Subscription, Plan
from django.db.models.functions import TruncMonth


User = get_user_model()


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
        
        # Get analyses for this month and last month
        today = now().date()
        start_of_month = today.replace(day=1)
        last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
        
        analyses_goals_this_month = [analysis.ratings.goals for analysis in analyses if analysis.created_at.date() >= start_of_month]
        analyses_goals_last_month = [analysis.ratings.goals for analysis in analyses if last_month_start <= analysis.created_at.date() < start_of_month]
        
        # Calculate average goals for this month and last month
        avg_goals_this_month = round(mean(analyses_goals_this_month), 2) if analyses_goals_this_month else 0
        avg_goals_last_month = round(mean(analyses_goals_last_month), 2) if analyses_goals_last_month else 0
        
        avarage_rating_list = []
        for analysis in analyses:
            ratings = [
                float(analysis.ratings.skin_quality or 0),
                float(analysis.ratings.jawline_definition or 0),
                float(analysis.ratings.cheekbone_structure or 0),
                float(analysis.ratings.eye_area or 0),
                float(analysis.ratings.facial_proportions or 0)
            ]
            avg_rating = sum(ratings) / 5
            avarage_rating_list.append(avg_rating)
        
        # Calculate improvement: last value minus average of all previous values
        improvement_from_last_two = 0
        if len(avarage_rating_list) >= 2:
            # Average of all values except the last one
            avg_without_last = round(sum(avarage_rating_list[:-1]) / len(avarage_rating_list[:-1]), 2)
            last = avarage_rating_list[-1]
            improvement_from_last_two = round(last - avg_without_last, 2)
        
        data = {
            "improvement_ratings": improvement_from_last_two,
            "since_at": user_created_at.strftime("%d %B"),
            "days_active": (now().date() - user_created_at.date()).days,
            "since_at_active": user_created_at.strftime("%d %B"),
            "goal_score": round(mean([analysis.ratings.goals for analysis in analyses]), 2) if analyses else 0,
            "this_month_improvement_goals": round(avg_goals_this_month - avg_goals_last_month, 2),
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



class UserOverviewView(APIView):
    def get(self, request, *args, **kwargs):
        total_analysis = ImageAnalysisResult.objects.count()
        total_user = User.objects.count()
        
        # Calculate total earnings from active subscriptions
        # Sum the plan amounts for all subscriptions with active or trialing status
        total_earnings = Subscription.objects.filter(
            status__in=['active', 'trialing']
        ).select_related('plan').aggregate(
            total=Sum('plan__amount')
        )['total'] or 0
        
        # Convert from cents to currency units (e.g., cents to euros/dollars)
        total_earnings = total_earnings / 100
        
        data = {
            "total_user": total_user,
            "total_earnings": total_earnings,
            "total_subscriptions": Subscription.objects.count(),
            "total_analysis": total_analysis,
        }
        
        return Response(data)
    
    
class UserGraph(APIView):
    def get(self, request, *args, **kwargs):

        # Calculate last 12 months range
        today = timezone.now().date().replace(day=1)
        months = []

        for i in range(12):
            month = today - datetime.timedelta(days=30 * i)
            months.append(month.replace(day=1))

        months = sorted(months)

        # Query signup counts grouped by month
        user_signups = (
            User.objects
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        # Convert to dict for fast lookup
        signup_dict = {entry["month"].date(): entry["count"] for entry in user_signups}

        # Build final 12-month output
        data = []
        for m in months:
            data.append({
                "month_year": m.strftime("%b-%Y"),
                "month_short": m.strftime("%b"),
                "count": signup_dict.get(m, 0) 
            })

        return Response({"user_signups": data})