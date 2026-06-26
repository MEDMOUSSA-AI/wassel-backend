from django.urls import path
from . import api

urlpatterns = [
    path("categories/",                    api.categories_list,        name="categories-list"),
    path("",                               api.restaurants_list,       name="restaurants-list"),
    path("<int:pk>/",                      api.restaurant_detail,      name="restaurant-detail"),
    path("mine/",                          api.my_restaurant,          name="my-restaurant"),
    path("mine/toggle-open/",              api.toggle_restaurant_open, name="toggle-open"),
    path("menus/",                         api.create_menu,            name="create-menu"),
    path("products/",                      api.create_product,         name="create-product"),
    path("products/<int:pk>/",             api.update_product,         name="update-product"),
    path("products/<int:pk>/delete/",      api.delete_product,         name="delete-product"),
    path("promotions/<int:pk>/",           api.promotion_detail,       name="promotion-detail"),
]
