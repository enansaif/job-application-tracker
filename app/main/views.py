from rest_framework.views import APIView
from main.serializers import TagSerializer, CountrySerializer
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.models import Tag, Country
from django.shortcuts import get_object_or_404


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
        return Response({"detail": "Tag deleted."}, status=status.HTTP_204_NO_CONTENT)


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
