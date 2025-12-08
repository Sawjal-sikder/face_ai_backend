from django.urls import path
from .image_analysis import *
from .views import *

urlpatterns = [
    path('analyze-image/', ImageAnalysis.as_view(), name='analyze-image'),
    path('analysis-list/', ImageAnalysisResultsListView.as_view(), name='analysis-results-list'),
    path('user-dashboard/', AnalysisResultsDashboardView.as_view(), name='analysis-results-user-dashboard'),
    path('progress-data/', ProgressView.as_view(), name='analysis-progress-data'),
    path('score-history/', ScoreHistoryView.as_view(), name='analysis-score-history'),
    path('detailed-metrics/', DetailedMetricsView.as_view(), name='analysis-detailed-metrics'),

    # Admin URLs
    path('admin/user-overview/', UserOverviewView.as_view(), name='admin-user-overview'),
    path('admin/user-graph/', UserGraph.as_view(), name='admin-user-graph'),
    path('admin/payment-graph/', PaymentGraph.as_view(), name='admin-payment-graph'),
    path('admin/user-management/', UserManagementView.as_view(), name='admin-user-management'),
]