from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os



class ImageAnalysis(APIView):
    def post(self, request, *args, **kwargs):
        image = request.FILES.get("image")

        if not image:
            return Response(
                {"message": "No image provided. Please upload an image."},
                status=status.HTTP_400_BAD_REQUEST
            )

        BASE_URL_AI = os.getenv('BASE_URL_AI')
        print(f"Using AI Base URL: {BASE_URL_AI}")

        return Response(
            {"message": "Image received successfully."},
            status=status.HTTP_200_OK
        )
