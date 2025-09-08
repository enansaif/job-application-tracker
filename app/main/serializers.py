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
    country_detail = CountrySerializer(source='country', read_only=True, required=False)
    tag_details = TagSerializer(source='tags', read_only=True, many=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=255),
        required=False,
        allow_empty=True,
        max_length=5,
        write_only=True
    )
    class Meta:
        model = Company
        fields = ['id', 'user', 'name', 'country', 'country_detail', 'link', 'tags', 'tag_details']
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
        for tag in tags:
            request = self.context.get('request')
            tag_obj, _ = Tag.objects.get_or_create(name=tag, user=request.user)
            obj_list.append(tag_obj)
        return obj_list

    @transaction.atomic
    def create(self, validated_data):
        tags_data = validated_data.pop('tags', None)
        company = super().create(validated_data)
        if tags_data:
            tags = self._handle_tags(tags_data)
            company.tags.set(tags)
        return company

    @transaction.atomic
    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        company = super().update(instance, validated_data)
        if tags_data:
            tags = self._handle_tags(tags_data)
            company.tags.set(tags)
        return company


class ResumeReadSerializer(ModelSerializer):
    tags = TagSerializer(many=True)
    class Meta:
        model = Resume
        fields = ['id', 'created_at', 'updated_at', 'tags']

    def create(self, validated_data):
        raise NotImplementedError("ResumeReadSerializer is read-only")

    def update(self, instance, validated_data):
        raise NotImplementedError("ResumeReadSerializer is read-only")


class ResumeWriteSerializer(ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length = 255),
        max_length = 5,
        write_only = True,
        required = False,
        allow_empty = True
    )
    class Meta:
        model = Resume
        fields = ['file', 'tags']

    def _handle_tags(self, tags):
        request = self.context.get('request')
        if not request:
            raise ValueError('Request must be passed in context')
        objs = []
        for tag in tags:
            obj, _ = Tag.objects.get_or_create(user=request.user, name=tag)
            objs.append(obj)
        return objs

    def validate_file(self, value):
        if value.content_type != 'application/pdf':
            raise serializers.ValidationError('Only PDF files are allowed.')
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError('File is not a pdf.')
        try:
            value.seek(0)
            file_header = value.read(4)
        except Exception:
            raise serializers.ValidationError("File couldn't be read")
        finally:
            value.seek(0)
        if file_header != b'%PDF':
            raise serializers.ValidationError('File is not a pdf!')
        return value

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags', None)
        request = self.context.get('request')
        if not request:
            raise ValueError('Request must be passed in context')
        resume = Resume.objects.create(**validated_data, user=request.user)
        if tags:
            tag_objs = self._handle_tags(tags)
            resume.tags.set(tag_objs)
        return resume

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        request = self.context.get('request')
        if not request:
            raise ValueError('Request must be passed in context')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            tag_objs = self._handle_tags(tags)
            instance.tags.set(tag_objs)
        return instance


class ApplicationSerializer(ModelSerializer):
    company = CompanySerializer(read_only=True)
    country = CountrySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), source="company", write_only=True
    )
    country_id = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), source="country",
        required=False, allow_null=True, write_only=True
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source="tags", many=True,
        required=False, write_only=True, allow_empty=True
    )
    resume_id = serializers.PrimaryKeyRelatedField(
        queryset=Resume.objects.all(), source="resume",
        required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = Application
        fields = [
            "id", "company", "country", "tags",
            "company_id", "country_id", "tag_ids", "resume_id",
            "position", "link", "note", "status",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if not request:
            raise ValueError("Request must be passed in context")
        tags = validated_data.pop("tags", None)
        application = Application.objects.create(**validated_data, user=request.user)
        if tags is not None:
            application.tags.set(tags)
        return application

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        instance = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.set(tags)
        return instance

class InterviewReadSerializer(serializers.ModelSerializer):
    application = ApplicationSerializer()
    tags = TagSerializer(many=True)

    class Meta:
        model = Interview
        fields = ['application', 'tags', 'date', 'note']

    def create(self, validated_data):
        raise NotImplementedError('This class is read only')

    def update(self, instance, validated_data):
        raise NotImplementedError('This class is read only')