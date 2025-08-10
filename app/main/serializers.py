from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from core import models


class TagSerializer(ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = models.Tag
        fields = ['id', 'name', 'user']
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=models.Tag.objects.all(),
                fields=['name', 'user'],
                message='Names need to be unique for every user'
            )
        ]


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
