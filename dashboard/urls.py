from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.home, name="home"),

    path("restaurants/", views.restaurants_list, name="restaurants"),
    path("restaurants/add/", views.restaurant_create, name="restaurant_create"),
    path("restaurants/<int:pk>/", views.restaurant_detail, name="restaurant_detail"),
    path("restaurants/<int:restaurant_pk>/products/add/", views.product_create, name="product_create"),

    path("livreurs/", views.livreurs_list, name="livreurs"),
    path("livreurs/add/", views.livreur_create, name="livreur_create"),
    path("livreurs/<int:pk>/", views.livreur_detail, name="livreur_detail"),

    path("orders/", views.orders_list, name="orders"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),

    path("clients/", views.clients_list, name="clients"),

    path("categories/", views.categories_list, name="categories"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
]
