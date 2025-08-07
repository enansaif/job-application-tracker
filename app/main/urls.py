from django.urls import path
from main import views

urlpatterns = [
    path('', views.TagListCreateView.as_view(), name='tags-list-create'),
    path('<id>/', views.TagUpdateDestroyView.as_view(), name='tags-update-destroy')
]