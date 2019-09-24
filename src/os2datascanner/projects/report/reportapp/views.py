from django.shortcuts import render
from rest_framework import generics
from .models import DocumentReport
from .serializers import DocumentReportSerializer
from django.views.generic import TemplateView 

# Create your views here.
class ReportView(generics.ListAPIView):
  queryset = DocumentReport.objects.all()
  serializer_class = DocumentReportSerializer

class MainPageView(TemplateView):
  template_name = 'index.html' 