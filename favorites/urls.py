from django.urls import path
from . import api

urlpatterns = [
    path('',         api.favorites_list,   name='favorites-list'),   # GET + POST
    path('<int:pk>/', api.favorites_detail, name='favorites-detail'), # DELETE
]
