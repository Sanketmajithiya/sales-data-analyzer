from django.urls import path
from .views import *

urlpatterns = [
    path('', upload_excel, name='upload_excel'),
    path('download/<str:file_type>/',download_analysis, name='download_analysis'),
]
