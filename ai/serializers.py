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
