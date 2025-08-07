from django.urls import path
from main.views import TagListCreateView

urlpatterns = [
    path('', TagListCreateView.as_view(), name='tags-list-create')
]