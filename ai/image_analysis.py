import os
import requests
from rest_framework import status
from rest_framework import permissions
from ai.models import ImageAnalysisResult
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ImageAnalysisResultSerializer
from payment.utils import deduct_analysis
from payment.models import analysesBalance
from payment.paymentpermission import HasActiveSubscription


class ImageAnalysis(APIView):
    permission_classes = [permissions.IsAuthenticated, HasActiveSubscription]
    
    def post(self, request, *args, **kwargs):
        # Check if user has available analyses and deduct one
        try:
            balance_obj = analysesBalance.objects.get(user=request.user)
            
            # Check if unlimited
            is_unlimited = balance_obj.balance >= 999999
            
            if is_unlimited:
                # Unlimited plan - allow analysis without deduction
                pass
            else:
                # Regular plan - check balance
                if balance_obj.balance <= 0:
                    return Response({
                        "message": "Insufficient analysis credits",
                        "details": "Please subscribe to a plan or upgrade to get more credits"
                    }, status=402)
                
                # Deduct 1 from balance
                balance_obj.balance -= 1
                balance_obj.save()
                
        except analysesBalance.DoesNotExist:
            return Response({
                "message": "No active subscription",
                "details": "Please subscribe to a plan to use this feature"
            }, status=402)
        
        image = request.FILES.get("image")

        if not image:
            return Response({"message": "No image provided"}, status=400)

        BASE_URL_AI = os.getenv('BASE_URL_AI')

        # Send image to AI server
        ai_response = requests.post(
            BASE_URL_AI,
            files={"file": (image.name, image.read(), image.content_type)}
        )

        if ai_response.status_code != 200:
            return Response({"message": "AI error", "details": ai_response.text}, status=500)

        data = ai_response.json()
        
        if data.get("face") == 0:
            return Response({"message": "Invalid face. Please upload a real human face."}, status=400)

        # Convert AI response to model structure
        payload = {
            "user": request.user.id if request.user.is_authenticated else None,
            "face": data["face"],
            "ratings": data["ratings"],  
            "key_strengths": data["key_strengths"],
            "exercise_guidance": data["exercise_guidance"],
            "ai_recommendations": data["ai_recommendations"],
        }

        serializer = ImageAnalysisResultSerializer(data=payload)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Image analyzed & saved", "data": serializer.data})

        return Response(serializer.errors, status=400)

