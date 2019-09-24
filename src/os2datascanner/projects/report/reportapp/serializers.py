from rest_framework import serializers
from .models import DocumentReport

class DocumentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentReport
        fields = ("path",)