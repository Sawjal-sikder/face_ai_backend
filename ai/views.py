from django.shortcuts import render
from rest_framework.generics import ListAPIView
from ai.models import ImageAnalysisResult
from .serializers import ImageAnalysisResultSerializer

# Create your views here.

class ImageAnalysisResultsListView(ListAPIView):
    queryset = ImageAnalysisResult.objects.all().order_by("-id")
    serializer_class = ImageAnalysisResultSerializer