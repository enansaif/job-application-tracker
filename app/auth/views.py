from rest_framework.views import APIView
from auth.serializers import AuthTokenSerializer
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status


class AuthTokenView(APIView):
    serializer_class = AuthTokenSerializer

    def post(self, request):
        serializer = AuthTokenSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
