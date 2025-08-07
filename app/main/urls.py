from django.urls import path
from main import views

urlpatterns = [
    path('tags/', views.TagListCreateView.as_view(), name='tags-list-create'),
    path('tags/<id>/', views.TagUpdateDestroyView.as_view(), name='tags-update-destroy')
]