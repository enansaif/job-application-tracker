from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from core.models import *
from django.db import transaction


class TagSerializer(ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Tag
        fields = ['id', 'name', 'user']
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Tag.objects.all(),
                fields=['name', 'user'],
                message='Names need to be unique for every user'
            )
        ]


class CountrySerializer(ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Country
        fields = ['id', 'name', 'user']
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Country.objects.all(),
                fields=['name', 'user'],
                message='Names need to be unique for every user'
            )
        ]


class CompanySerializer(ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    country = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(),
        required=False,
        write_only=True
    )
    country_detail = CountrySerializer(read_only=True, required=False)
    tags = TagSerializer(many=True, required=False)
    class Meta:
        model = Company
        fields = ['id', 'user', 'name', 'country', 'country_detail', 'link', 'tags']
        read_only_fields = ['id', 'country_detail']
        validators = [
            UniqueTogetherValidator(
                queryset=Company.objects.all(),
                fields=['user', 'name'],
                message='Trying to create duplicate country.'
            )
        ]

    def _handle_tags(self, tags):
        obj_list = []
        for tag_name in tags:
            request = self.context.get('request')
            tag, _ = Tag.objects.get_or_create(name=tag_name, user=request.user)
            obj_list.append(tag)
        return obj_list

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', None)
        company = super().create(validated_data)
        if tags_data:
            tags = self._handle_tags(tags_data)
            company.tags.set(tags)
        return company

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        company = super().update(instance, validated_data)
        if tags_data:
            tags = self._handle_tags(tags_data)
            company.tags.set(tags)
        return company
