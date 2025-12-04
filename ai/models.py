from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Ratings(models.Model):
    skin_quality = models.FloatField()
    jawline_definition = models.FloatField()
    cheekbone_structure = models.FloatField()
    eye_area = models.FloatField()
    facial_proportions = models.FloatField()
    symmetry = models.FloatField(default=0.0)
    goals = models.FloatField(default=0.0)

    def __str__(self):
        return f"Ratings (SQ={self.skin_quality})"


class ImageAnalysisResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    face = models.PositiveIntegerField()

    ratings = models.OneToOneField(Ratings, on_delete=models.CASCADE, related_name="analysis")

    key_strengths = models.JSONField(default=list)
    exercise_guidance = models.JSONField(default=list)
    ai_recommendations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis Result (Face={self.face})"
