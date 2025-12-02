from .image_analysis import ImageAnalysis
from django.urls import path
from . import views

urlpatterns = [
    path('analyze-image/', ImageAnalysis.as_view(), name='analyze-image'),
]