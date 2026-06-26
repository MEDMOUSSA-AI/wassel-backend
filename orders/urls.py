from django.urls import path
from . import api

urlpatterns = [
    path("food/",                    api.create_food_order,        name="create-food-order"),
    path("parcel/",                  api.create_parcel_order,      name="create-parcel-order"),
    path("my/",                      api.my_orders,                name="my-orders"),
    path("restaurant/",              api.restaurant_orders,        name="restaurant-orders"),
    path("<int:pk>/",                api.order_detail,             name="order-detail"),
    path("<int:pk>/confirm/",        api.restaurant_confirm_order, name="confirm-order"),
    path("<int:pk>/cancel/",         api.cancel_order,             name="cancel-order"),
    # ✅ تقييم المندوب بعد التوصيل — POST /api/orders/<pk>/rate/
    path("<int:pk>/rate/",           api.rate_order,               name="rate-order"),
]
