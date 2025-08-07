from rest_framework.serializers import ModelSerializer
from core import models


class TagSerializer(ModelSerializer):

    class Meta:
        model = models.Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

    def create(self, validated_data):
        request = self.context.get('request')
        tag, _ = models.Tag.objects.get_or_create(user=request.user, **validated_data)
        return tag