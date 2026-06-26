from django.urls import path
from . import api

urlpatterns = [
    path('',      api.promotions,       name='promotions-list'),
    path('<int:pk>/', api.promotion_detail, name='promotion-detail'),
]
