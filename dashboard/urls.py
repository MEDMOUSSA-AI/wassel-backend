from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("login/",  views.login_view,  name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("",        views.home,        name="home"),

    # ── المطاعم ──
    path("restaurants/",                                   views.restaurants_list,   name="restaurants"),
    path("restaurants/add/",                               views.restaurant_create,  name="restaurant_create"),
    path("restaurants/<int:pk>/",                          views.restaurant_detail,  name="restaurant_detail"),
    path("restaurants/<int:pk>/edit/",                     views.restaurant_edit,    name="restaurant_edit"),
    path("restaurants/<int:pk>/delete/",                   views.restaurant_delete,  name="restaurant_delete"),

    # ── المنتجات ──
    path("restaurants/<int:restaurant_pk>/products/add/",  views.product_create,     name="product_create"),
    path("products/<int:pk>/edit/",                        views.product_edit,       name="product_edit"),
    path("products/<int:pk>/delete/",                      views.product_delete,     name="product_delete"),

    # ── المناديب ──
    path("livreurs/",                 views.livreurs_list,  name="livreurs"),
    path("livreurs/add/",             views.livreur_create, name="livreur_create"),
    path("livreurs/<int:pk>/",        views.livreur_detail, name="livreur_detail"),
    path("livreurs/<int:pk>/edit/",   views.livreur_edit,   name="livreur_edit"),
    path("livreurs/<int:pk>/delete/", views.livreur_delete, name="livreur_delete"),

    # ── الطلبات ──
    path("orders/",          views.orders_list,  name="orders"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),

    # ── العملاء ──
    path("clients/", views.clients_list, name="clients"),

    # ── الفئات ──
    path("categories/",                  views.categories_list, name="categories"),
    path("categories/<int:pk>/delete/",  views.category_delete, name="category_delete"),
    path("categories/<int:pk>/edit/",    views.category_edit,   name="category_edit"),   # ← جديد
]
