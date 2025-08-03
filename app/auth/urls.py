from django.urls import path
from auth.views import AuthTokenView

urlpatterns = [
    path('token/', AuthTokenView.as_view(), name='token')
]
