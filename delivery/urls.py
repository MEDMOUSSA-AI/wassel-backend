from django.urls import path
from . import api

urlpatterns = [
    path("available/",               api.available_orders,      name="available-orders"),
    path("toggle-online/",           api.toggle_online,         name="toggle-online"),
    path("my-orders/",               api.my_deliveries,         name="my-deliveries"),
    path("balance/",                 api.my_balance,            name="my-balance"),
    path("<int:order_id>/accept/",   api.accept_order,          name="accept-order"),
    path("<int:order_id>/status/",   api.update_order_status,   name="update-status"),
    path("<int:order_id>/location/", api.update_location,       name="update-location"),
    path("<int:order_id>/location/get/", api.get_livreur_location, name="get-location"),
]