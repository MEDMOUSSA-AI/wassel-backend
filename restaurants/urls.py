from django.urls import path
from . import api

urlpatterns = [
    path("categories/",               api.categories_list,        name="categories-list"),
    path("",                          api.restaurants_list,       name="restaurants-list"),
    path("<int:pk>/",                 api.restaurant_detail,      name="restaurant-detail"),
    path("mine/",                     api.my_restaurant,          name="my-restaurant"),
    path("mine/toggle-open/",         api.toggle_restaurant_open, name="toggle-open"),
    path("menus/",                    api.create_menu,            name="create-menu"),
    path("menus/<int:pk>/",           api.update_menu,            name="update-menu"),
    path("menus/<int:pk>/delete/",    api.delete_menu,            name="delete-menu"),
    path("products/",                 api.create_product,         name="create-product"),
    path("products/<int:pk>/",        api.update_product,         name="update-product"),
    path("products/<int:pk>/delete/", api.delete_product,         name="delete-product"),
    path("promotions/",               api.promotions,             name="promotions-list"),
    path("promotions/<int:pk>/",      api.promotion_detail,       name="promotion-detail"),
    # ⚠️ مؤقت — احذفهما بعد الانتهاء
    path("migrate-images/",           api.migrate_images,         name="migrate-images"),
    path("clear-broken-images/",      api.clear_broken_images,    name="clear-broken-images"),
]
