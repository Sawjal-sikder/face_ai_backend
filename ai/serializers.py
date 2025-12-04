from rest_framework import serializers
from .models import ImageAnalysisResult, Ratings


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
            ]

    def create(self, validated_data):
        ratings_data = validated_data.pop("ratings")
        ratings = Ratings.objects.create(**ratings_data)
        result = ImageAnalysisResult.objects.create(ratings=ratings, **validated_data)
        return result
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        avg = (
            instance.ratings.skin_quality +
            instance.ratings.jawline_definition +
            instance.ratings.cheekbone_structure +
            instance.ratings.eye_area +
            instance.ratings.facial_proportions
        ) / 5
        representation['average_rating'] = format(avg, ".2f")
        representation['user'] = instance.user.full_name if instance.user else None
        return representation
