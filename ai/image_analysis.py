import os
import requests

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ImageAnalysisResultSerializer
from payment.models import AnalysisCreditTransaction
from payment.paymentpermission import HasActiveSubscription
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from ai.models import ImageAnalysisResult


class ImageAnalysis(APIView):
    permission_classes = [permissions.IsAuthenticated, HasActiveSubscription]

    def post(self, request, *args, **kwargs):

        image = request.FILES.get("image")
        if not image:
            return Response({"message": "No image provided"}, status=400)

        BASE_URL_AI = os.getenv("BASE_URL_AI")

        ai_response = requests.post(
            BASE_URL_AI,
            files={"file": (image.name, image.read(), image.content_type)}
        )

        if ai_response.status_code != 200:
            return Response({
                "message": "AI error",
                "details": ai_response.text
            }, status=500)

        data = ai_response.json()

        if data.get("face") == 0:
            return Response({
                "message": "Invalid face. Please upload a real human face."
            }, status=400)

        # Everything succeeded → now deduct safely
        AnalysisCreditTransaction.objects.create(
            user=request.user,
            credits=1,
            type="use",
            reason="Used for image analysis.",
        )

        payload = {
                "user": request.user.id,
                "face": data["face"],
                "ratings": data["ratings"],
                "key_strengths": data["key_strengths"],
                "exercise_guidance": data["exercise_guidance"],
                "ai_recommendations": data["ai_recommendations"],
            }

        serializer = ImageAnalysisResultSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Image analyzed & saved",
            "data": serializer.data
        })

