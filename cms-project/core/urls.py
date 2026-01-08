"""
URL patterns for the core app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('complaints/', views.complaint_list, name='complaint_list'),
    path('complaints/new/', views.complaint_create, name='complaint_create'),
    path('complaints/<int:pk>/', views.complaint_detail, name='complaint_detail'),
    path('complaints/<int:pk>/status/', views.complaint_update_status, name='complaint_update_status'),
    path('complaints/<int:pk>/assign/', views.complaint_assign, name='complaint_assign'),
    path('complaints/<int:pk>/resolution/', views.complaint_add_resolution, name='complaint_add_resolution'),
    path('complaints/<int:pk>/close/', views.complaint_close, name='complaint_close'),
]
