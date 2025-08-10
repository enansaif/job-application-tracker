from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
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

class CountrySerializer(ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = models.Country
        fields = ['id', 'name', 'user']
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=models.Country.objects.all(),
                fields=['name', 'user'],
                message='Names need to be unique for every user'
            )
        ]
