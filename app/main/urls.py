from django.urls import path
from main import views

urlpatterns = [
    path('tags/', views.TagListCreateView.as_view(), name='tags-list-create'),
    path('tags/<int:id>/', views.TagUpdateDestroyView.as_view(), name='tags-update-destroy'),
    path('country/', views.CountryListCreateView.as_view(), name='country-list-create'),
    path('country/<int:id>/', views.CountryUpdateDestroy.as_view(), name='country-update-destroy'),
    path('company/', views.CompanyListView.as_view(), name='company-list-create'),
    path('company/<int:id>', views.CompanyDetailView.as_view(), name='company-update-destroy')
]