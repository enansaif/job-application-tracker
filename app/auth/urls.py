from django.urls import path
from auth.views import AuthTokenView, UserDetailView, UserRegisterView

urlpatterns = [
    path('token/', AuthTokenView.as_view(), name='token'),
    path('me/', UserDetailView.as_view(), name='me'),
    path('register/', UserRegisterView.as_view(), name='register')
]
