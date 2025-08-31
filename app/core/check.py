from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
from drf_spectacular.utils import extend_schema

class HealthCheckSerializer(serializers.Serializer):
    serializers.CharField(read_only=True)


@extend_schema(responses=HealthCheckSerializer)
@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok"})
