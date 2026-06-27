"""
orders/api.py — API الطلبات (طعام + طرود)
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from accounts.models import User
from restaurants.models import Product, Restaurant
from .models import Order, OrderItem, OrderStatusHistory


def _order_dict(order, request=None):
    """تحويل طلب إلى dict قابل للإرسال."""
    items = [
        {
            "id":           i.id,
            "product_name": i.product_name,
            "unit_price":   float(i.unit_price),
            "quantity":     i.quantity,
            "subtotal":     float(i.subtotal),
        }
        for i in order.items.all()
    ]
    return {
        "id":                order.id,
        "order_type":        order.order_type,
        "status":            order.status,
        "pickup_address":    order.pickup_address,
        "pickup_lat":        order.pickup_lat,
        "pickup_lng":        order.pickup_lng,
        "dropoff_address":   order.dropoff_address,
        "dropoff_lat":       order.dropoff_lat,
        "dropoff_lng":       order.dropoff_lng,
        "items_price":       float(order.items_price),
        "delivery_fee":      float(order.delivery_fee),
        "total_price":       float(order.total_price),
        "distance_km":       order.distance_km,
        "estimated_minutes": order.estimated_minutes,
        "payment_method":    order.payment_method,
        "rating":            order.rating,
        "restaurant":        {"id": order.restaurant.id, "name": order.restaurant.name} if order.restaurant else None,
        "livreur":           {"id": order.livreur.id, "full_name": order.livreur.full_name} if order.livreur else None,
        "items":             items,
        "created_at":        order.created_at.isoformat(),
    }


# ─────────────────────────────────────────────
# إنشاء طلب طعام
# POST /api/orders/food/
# ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_food_order(request):
    import traceback
    try:
        if request.user.role != User.Role.CLIENT:
            return Response({"detail": "فقط العملاء يمكنهم إنشاء طلبات."}, status=403)

        restaurant_id     = request.data.get("restaurant_id")
        items_data        = request.data.get("items", [])
        dropoff_address   = request.data.get("dropoff_address", "").strip()
        dropoff_lat       = request.data.get("dropoff_lat")
        dropoff_lng       = request.data.get("dropoff_lng")
        delivery_fee      = request.data.get("delivery_fee", 0)
        distance_km       = request.data.get("distance_km")
        estimated_minutes = request.data.get("estimated_minutes")

        if not restaurant_id or not items_data or not dropoff_address:
            return Response({"detail": "restaurant_id و items و dropoff_address مطلوبة."}, status=400)

        restaurant = get_object_or_404(Restaurant, pk=restaurant_id, approval_status="approved")

        items_price = 0
        order_items = []
        for item in items_data:
            product    = get_object_or_404(Product, pk=item.get("product_id"))
            qty        = int(item.get("quantity", 1))
            unit_price = float(product.final_price)
            items_price += unit_price * qty
            order_items.append((product, qty, unit_price))

        total_price = items_price + float(delivery_fee)

        order = Order.objects.create(
            order_type=Order.OrderType.FOOD,
            client=request.user,
            restaurant=restaurant,
            status=Order.Status.PENDING,
            pickup_address=restaurant.address,
            pickup_lat=restaurant.lat or 0,
            pickup_lng=restaurant.lng or 0,
            dropoff_address=dropoff_address,
            dropoff_lat=dropoff_lat,
            dropoff_lng=dropoff_lng,
            items_price=items_price,
            delivery_fee=delivery_fee,
            total_price=total_price,
            distance_km=distance_km,
            estimated_minutes=estimated_minutes,
        )

        for product, qty, unit_price in order_items:
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                unit_price=unit_price,
                quantity=qty,
            )

        OrderStatusHistory.objects.create(order=order, status=Order.Status.PENDING)
        return Response(_order_dict(order), status=201)

    except Exception as e:
        return Response({
            "detail": str(e),
            "trace":  traceback.format_exc(),
        }, status=500)


# ─────────────────────────────────────────────
# إنشاء طلب طرد
# POST /api/orders/parcel/
# ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_parcel_order(request):
    if request.user.role != User.Role.CLIENT:
        return Response({"detail": "فقط العملاء يمكنهم إنشاء طلبات."}, status=403)

    required_fields = ["pickup_address", "pickup_lat", "pickup_lng",
                       "dropoff_address", "dropoff_lat", "dropoff_lng", "delivery_fee"]
    for f in required_fields:
        if not request.data.get(f):
            return Response({"detail": f"الحقل '{f}' مطلوب."}, status=400)

    delivery_fee = float(request.data["delivery_fee"])

    order = Order.objects.create(
        order_type=Order.OrderType.PARCEL,
        client=request.user,
        status=Order.Status.SEARCHING_LIVREUR,
        pickup_address=request.data["pickup_address"],
        pickup_lat=request.data["pickup_lat"],
        pickup_lng=request.data["pickup_lng"],
        dropoff_address=request.data["dropoff_address"],
        dropoff_lat=request.data["dropoff_lat"],
        dropoff_lng=request.data["dropoff_lng"],
        recipient_name=request.data.get("recipient_name", ""),
        recipient_phone=request.data.get("recipient_phone", ""),
        parcel_notes=request.data.get("parcel_notes", ""),
        delivery_fee=delivery_fee,
        total_price=delivery_fee,
        distance_km=request.data.get("distance_km"),
        estimated_minutes=request.data.get("estimated_minutes"),
    )

    OrderStatusHistory.objects.create(order=order, status=Order.Status.SEARCHING_LIVREUR)
    return Response(_order_dict(order), status=201)


# ─────────────────────────────────────────────
# طلبات العميل
# GET /api/orders/my/
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_orders(request):
    orders = Order.objects.filter(client=request.user).order_by("-created_at")
    return Response([_order_dict(o) for o in orders])


# ─────────────────────────────────────────────
# تفاصيل طلب واحد
# GET /api/orders/<id>/
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    user  = request.user
    order = get_object_or_404(Order, pk=pk)

    if not (
        order.client == user
        or (user.role == User.Role.RESTAURANT and hasattr(user, "restaurant") and order.restaurant == user.restaurant)
        or (user.role == User.Role.LIVREUR and order.livreur == user)
        or user.role == User.Role.ADMIN
    ):
        return Response({"detail": "غير مصرح."}, status=403)

    return Response(_order_dict(order))


# ─────────────────────────────────────────────
# تأكيد الطلب من المطعم
# PATCH /api/orders/<id>/confirm/
# ─────────────────────────────────────────────
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def restaurant_confirm_order(request, pk):
    if request.user.role != User.Role.RESTAURANT:
        return Response({"detail": "غير مصرح."}, status=403)

    order = get_object_or_404(
        Order, pk=pk, restaurant__owner=request.user, order_type=Order.OrderType.FOOD
    )

    if order.status != Order.Status.PENDING:
        return Response({"detail": "الطلب ليس في حالة انتظار."}, status=400)

    order.status = Order.Status.SEARCHING_LIVREUR
    order.save(update_fields=["status"])
    OrderStatusHistory.objects.create(order=order, status=order.status)
    return Response({"status": order.status})


# ─────────────────────────────────────────────
# إلغاء الطلب
# PATCH /api/orders/<id>/cancel/
# ─────────────────────────────────────────────
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, client=request.user)

    if order.status not in [Order.Status.PENDING, Order.Status.SEARCHING_LIVREUR]:
        return Response({"detail": "لا يمكن إلغاء الطلب في هذه المرحلة."}, status=400)

    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status"])
    OrderStatusHistory.objects.create(order=order, status=Order.Status.CANCELLED)
    return Response({"status": order.status})


# ─────────────────────────────────────────────
# طلبات المطعم
# GET /api/orders/restaurant/
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def restaurant_orders(request):
    if request.user.role != User.Role.RESTAURANT:
        return Response({"detail": "غير مصرح."}, status=403)

    restaurant = get_object_or_404(Restaurant, owner=request.user)
    orders     = Order.objects.filter(restaurant=restaurant).order_by("-created_at")
    return Response([_order_dict(o) for o in orders])


# ─────────────────────────────────────────────
# تقييم المندوب بعد التوصيل
# POST /api/orders/<id>/rate/
# body: { "rating": 4.5 }
# ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rate_order(request, pk):
    order = get_object_or_404(
        Order, pk=pk, client=request.user, status=Order.Status.DELIVERED
    )

    if order.rating is not None:
        return Response({"detail": "تم تقييم هذا الطلب مسبقاً."}, status=400)

    rating = request.data.get("rating")
    if rating is None:
        return Response({"detail": "rating مطلوب."}, status=400)

    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return Response({"detail": "rating يجب أن يكون رقماً."}, status=400)

    if not (1.0 <= rating <= 5.0):
        return Response({"detail": "rating يجب أن يكون بين 1 و 5."}, status=400)

    order.rating = rating
    order.save(update_fields=["rating"])

    return Response({"detail": "تم التقييم بنجاح.", "rating": order.rating})
