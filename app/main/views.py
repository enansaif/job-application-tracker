from rest_framework.views import APIView
from main.serializers import *
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.models import Tag, Country
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import MultiPartParser, FormParser


class TagListCreateView(APIView):
    serializer_class = TagSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tags = Tag.objects.filter(user=request.user)
        serializer = TagSerializer(instance=tags, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TagSerializer(data=request.data, context = {'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TagUpdateDestroyView(APIView):
    serializer_class = TagSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        tag = get_object_or_404(Tag, id=id, user=request.user)
        serializer = TagSerializer(instance=tag, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        tag = get_object_or_404(Tag, id=id, user=request.user)
        tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CountryListCreateView(APIView):
    serializer_class = CountrySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        countries = Country.objects.filter(user=request.user)
        serializer = CountrySerializer(instance=countries, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CountrySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CountryUpdateDestroy(APIView):
    serializer_class = CountrySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        country = get_object_or_404(Country, id=id, user=request.user)
        serializer = CountrySerializer(instance=country, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, id):
        country = get_object_or_404(Country, id=id, user=request.user)
        country.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyListView(APIView):
    serializer_class = CompanySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        companies = Company.objects.filter(user=request.user)
        serializer = CompanySerializer(many=True, instance=companies)
        return Response(serializer.data)

    def post(self, request):
        serializer = CompanySerializer(data=request.data, context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CompanyDetailView(APIView):
    serializer_class = CompanySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        company = get_object_or_404(Company, id=id, user=request.user)
        serializer = CompanySerializer(instance=company)
        return Response(serializer.data)

    def patch(self, request, id):
        company = get_object_or_404(Company, id=id, user=request.user)
        serializer = CompanySerializer(instance=company, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        company = get_object_or_404(Company, id=id, user=request.user)
        company.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ResumeDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=ResumeReadSerializer
    )
    def get(self, request, id):
        resume = get_object_or_404(Resume, id=id, user=request.user)
        serializer = ResumeReadSerializer(resume)
        return Response(serializer.data)

    @extend_schema(
        request=ResumeWriteSerializer,
        responses=ResumeReadSerializer
    )
    def patch(self, request, id):
        resume = get_object_or_404(Resume, id=id, user=request.user)
        serializer = ResumeWriteSerializer(instance=resume, data=request.data, partial=True)
        if serializer.is_valid():
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResumeListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        responses=ResumeReadSerializer
    )
    def get(self, request):
        resumes = Resume.objects.filter(user=request.user)
        serializer = ResumeReadSerializer(resumes, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=ResumeWriteSerializer,
        responses=ResumeReadSerializer
    )
    def post(self, request):
        serializer = ResumeWriteSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            resume = serializer.save()
            return Response(ResumeReadSerializer(resume).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)