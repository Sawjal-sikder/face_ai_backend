from django.urls import path
from .image_analysis import *
from .views import *

urlpatterns = [
    path('analyze-image/', ImageAnalysis.as_view(), name='analyze-image'),
    path('analysis-list/', ImageAnalysisResultsListView.as_view(), name='analysis-results-list'),
    path('user-dashboard/', AnalysisResultsDashboardView.as_view(), name='analysis-results-user-dashboard'),
]