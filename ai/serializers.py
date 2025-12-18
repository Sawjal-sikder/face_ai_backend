from rest_framework import serializers
from .models import ImageAnalysisResult, Ratings
from django.contrib.auth import get_user_model


User = get_user_model()

class RatingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ratings
        fields = "__all__"


class ImageAnalysisResultSerializer(serializers.ModelSerializer):
    ratings = RatingsSerializer()

    class Meta:
        model = ImageAnalysisResult
        # fields = "__all__"
        fields = [
            "id",
            "user",
            "face",
            "ratings",
            "key_strengths",
            "exercise_guidance",
            "ai_recommendations",
            "created_at"
            ]

    def create(self, validated_data):
        ratings_data = validated_data.pop("ratings")
        ratings = Ratings.objects.create(**ratings_data)
        result = ImageAnalysisResult.objects.create(ratings=ratings, **validated_data)
        return result
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Ensure all rating fields are numeric before calculation
        ratings = [
            float(instance.ratings.skin_quality or 0),
            float(instance.ratings.jawline_definition or 0),
            float(instance.ratings.cheekbone_structure or 0),
            float(instance.ratings.eye_area or 0),
            float(instance.ratings.facial_proportions or 0)
        ]
        avg = sum(ratings) / 5
        representation['average_rating'] = round(avg, 2)  # Keep as float, not string
        representation['user'] = instance.user.full_name if instance.user else None
        return representation



class UserManagementSerializer(serializers.ModelSerializer):
    image_analysis = ImageAnalysisResultSerializer(many=True, read_only=True, source='imageanalysisresult_set')
    total_analyses = serializers.SerializerMethodField()
    subscription_plan = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ["id", "full_name", "email", "phone_number", "total_analyses" , "subscription_plan" ,"image_analysis"]
    
    def get_total_analyses(self, obj):
        return obj.imageanalysisresult_set.count()
    
    def get_subscription_plan(self, obj):
        latest_subscription = obj.subscriptions.order_by('-created_at').first()
        if latest_subscription and latest_subscription.plan:
            return latest_subscription.plan.name
        return None