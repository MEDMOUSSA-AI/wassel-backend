"""
delivery/api.py — API المندوب (قبول/رفض طلب، تحديث الحالة، الموقع)
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg, Sum

from accounts.models import User, LivreurProfile
from orders.models import Order, OrderStatusHistory
from .models import LiveTrackingPoint


# ─────────────────────────────────────────────
# الطلبات المتاحة للمندوب (بانتظار مندوب)
# GET /api/delivery/available/
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def available_orders(request):
    if request.user.role != User.Role.LIVREUR:
        return Response({"detail": "غير مصرح."}, status=403)

    profile = get_object_or_404(LivreurProfile, user=request.user)
    if profile.approval_status != "approved":
        return Response({"detail": "حسابك قيد المراجعة."}, status=403)

    orders = Order.objects.filter(
        status=Order.Status.SEARCHING_LIVREUR,
        livreur__isnull=True,
    ).order_by("-created_at")

    data = [
        {
            "id":                o.id,
            "order_type":        o.order_type,
            "pickup_address":    o.pickup_address,
            "pickup_lat":        o.pickup_lat,
            "pickup_lng":        o.pickup_lng,
            "dropoff_address":   o.dropoff_address,
            "dropoff_lat":       o.dropoff_lat,
            "dropoff_lng":       o.dropoff_lng,
            "delivery_fee":      float(o.delivery_fee),
            "distance_km":       o.distance_km,
            "estimated_minutes": o.estimated_minutes,
            "restaurant":        {"id": o.restaurant.id, "name": o.restaurant.name} if o.restaurant else None,
        }
        for o in orders
    ]
    return Response(data)


# ─────────────────────────────────────────────
# قبول طلب من المندوب
# POST /api/delivery/<order_id>/accept/
# ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_order(request, order_id):
    if request.user.role != User.Role.LIVREUR:
        return Response({"detail": "غير مصرح."}, status=403)

    profile = get_object_or_404(LivreurProfile, user=request.user)
    if profile.approval_status != "approved":
        return Response({"detail": "حسابك قيد المراجعة."}, status=403)

    order = get_object_or_404(
        Order,
        pk=order_id,
        status=Order.Status.SEARCHING_LIVREUR,
        livreur__isnull=True,
    )

    order.livreur = request.user
    order.status  = Order.Status.ACCEPTED
    order.save(update_fields=["livreur", "status"])
    OrderStatusHistory.objects.create(order=order, status=Order.Status.ACCEPTED)

    return Response({"status": order.status, "order_id": order.id})


# ─────────────────────────────────────────────
# تحديث حالة الطلب من المندوب
# PATCH /api/delivery/<order_id>/status/
# body: { "status": "picked_up" | "on_the_way" | "delivered" }
# ─────────────────────────────────────────────
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    if request.user.role != User.Role.LIVREUR:
        return Response({"detail": "غير مصرح."}, status=403)

    order = get_object_or_404(Order, pk=order_id, livreur=request.user)

    allowed_transitions = {
        Order.Status.ACCEPTED:   [Order.Status.PICKED_UP],
        Order.Status.PICKED_UP:  [Order.Status.ON_THE_WAY],
        Order.Status.ON_THE_WAY: [Order.Status.DELIVERED],
    }

    new_status = request.data.get("status")
    if new_status not in [s.value for s in Order.Status]:
        return Response({"detail": "حالة غير صالحة."}, status=400)

    allowed = [s.value for s in allowed_transitions.get(order.status, [])]
    if new_status not in allowed:
        return Response(
            {"detail": f"لا يمكن الانتقال من '{order.status}' إلى '{new_status}'."},
            status=400,
        )

    order.status = new_status
    order.save(update_fields=["status"])
    OrderStatusHistory.objects.create(order=order, status=new_status)

    # إذا تم التوصيل، أضف الرصيد للمندوب
    if new_status == Order.Status.DELIVERED:
        profile = request.user.livreur_profile
        profile.balance += order.livreur_net_fee
        profile.save(update_fields=["balance"])

    return Response({"status": order.status})


# ─────────────────────────────────────────────
# تحديث موقع المندوب أثناء التوصيل
# POST /api/delivery/<order_id>/location/
# body: { "lat": 18.07, "lng": -15.95 }
# ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_location(request, order_id):
    if request.user.role != User.Role.LIVREUR:
        return Response({"detail": "غير مصرح."}, status=403)

    order = get_object_or_404(Order, pk=order_id, livreur=request.user)

    lat = request.data.get("lat")
    lng = request.data.get("lng")
    if lat is None or lng is None:
        return Response({"detail": "lat و lng مطلوبان."}, status=400)

    profile = request.user.livreur_profile
    profile.current_lat = lat
    profile.current_lng = lng
    profile.save(update_fields=["current_lat", "current_lng"])

    LiveTrackingPoint.objects.create(order=order, lat=lat, lng=lng)

    return Response({"detail": "تم تحديث الموقع."})


# ─────────────────────────────────────────────
# آخر موقع للمندوب (للعميل في شاشة التتبع)
# GET /api/delivery/<order_id>/location/get/
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_livreur_location(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    if order.client != request.user and order.livreur != request.user:
        return Response({"detail": "غير مصرح."}, status=403)

    point = LiveTrackingPoint.objects.filter(order=order).first()
    if not point:
        return Response({"detail": "لا يوجد موقع بعد."}, status=404)

    return Response({
        "lat":       point.lat,
        "lng":       point.lng,
        "timestamp": point.timestamp.isoformat(),
    })


# ─────────────────────────────────────────────
# تفعيل/تعطيل حالة المندوب (متاح/غير متاح)
# PATCH /api/delivery/toggle-online/
# ─────────────────────────────────────────────
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def toggle_online(request):
    if request.user.role != User.Role.LIVREUR:
        return Response({"detail": "غير مصرح."}, status=403)

    profile = get_object_or_404(LivreurProfile, user=request.user)
    profile.is_online = not profile.is_online
    profile.save(update_fields=["is_online"])
    return Response({"is_online": profile.is_online})


# ─────────────────────────────────────────────
# طلبات المندوب الحالية والسابقة
# GET /api/delivery/my-orders/
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_deliveries(request):
    if request.user.role != User.Role.LIVREUR:
        return Response({"detail": "غير مصرح."}, status=403)

    orders = (
        Order.objects
        .filter(livreur=request.user)
        .select_related("restaurant")
        .prefetch_related("status_history")
        .order_by("-created_at")
    )

    data = []
    for o in orders:
        delivered_record = next(
            (h for h in sorted(o.status_history.all(), key=lambda h: h.timestamp, reverse=True)
             if h.status == Order.Status.DELIVERED),
            None,
        )
        data.append({
            "id":                o.id,
            "order_type":        o.order_type,
            "status":            o.status,
            "restaurant":        {"id": o.restaurant.id, "name": o.restaurant.name} if o.restaurant else None,
            "pickup_address":    o.pickup_address,
            "dropoff_address":   o.dropoff_address,
            "items_total":       float(o.items_price),
            "delivery_fee":      float(o.delivery_fee),
            "net_fee":           float(o.livreur_net_fee),
            "distance_km":       o.distance_km,
            "estimated_minutes": o.estimated_minutes,
            "created_at":        o.created_at.isoformat(),
            "delivered_at":      delivered_record.timestamp.isoformat() if delivered_record else None,
        })

    return Response(data)


# ─────────────────────────────────────────────
# رصيد المندوب مع إحصائيات الأسبوع والتقييم
# GET /api/delivery/balance/
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_balance(request):
    if request.user.role != User.Role.LIVREUR:
        return Response({"detail": "غير مصرح."}, status=403)

    profile = get_object_or_404(LivreurProfile, user=request.user)

    # ── اليوم ──
    today = timezone.localdate()
    today_count = (
        Order.objects
        .filter(
            livreur=request.user,
            status=Order.Status.DELIVERED,
            status_history__status=Order.Status.DELIVERED,
            status_history__timestamp__date=today,
        )
        .distinct()
        .count()
    )

    # ── بداية الأسبوع الحالي (الإثنين) ──
    week_start = today - timezone.timedelta(days=today.weekday())

    delivered_this_week = Order.objects.filter(
        livreur=request.user,
        status=Order.Status.DELIVERED,
        status_history__status=Order.Status.DELIVERED,
        status_history__timestamp__date__gte=week_start,
    ).distinct()

    # مجموع رسوم التوصيل الإجمالية (قبل العمولة) هذا الأسبوع
    weekly_earnings_before_commission = (
        delivered_this_week
        .aggregate(total=Sum("delivery_fee"))["total"] or 0
    )

    # مجموع ما وصل للمندوب فعلياً (بعد العمولة) هذا الأسبوع
    weekly_earnings = (
        delivered_this_week
        .aggregate(total=Sum("livreur_net_fee"))["total"] or 0
    )

    # ── متوسط التقييم ──
    # نفترض وجود حقل rating في Order يُملأ من قِبل العميل
    # إذا لم يكن موجوداً بعد يُرجع null
    avg_rating_result = (
        Order.objects
        .filter(
            livreur=request.user,
            status=Order.Status.DELIVERED,
            rating__isnull=False,
        )
        .aggregate(avg=Avg("rating"))["avg"]
    )
    average_rating = round(float(avg_rating_result), 2) if avg_rating_result else None

    return Response({
        "balance":                          float(profile.balance),
        "commission_rate":                  float(profile.commission_rate),
        "is_online":                        profile.is_online,
        "today_count":                      today_count,
        # ✅ جديد
        "weekly_earnings":                  float(weekly_earnings),
        "weekly_earnings_before_commission": float(weekly_earnings_before_commission),
        "average_rating":                   average_rating,
    })
