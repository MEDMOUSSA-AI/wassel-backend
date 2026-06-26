"""
restaurants/api.py — API المطاعم والقوائم والمنتجات
المسار: restaurants/api.py
"""
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count

from accounts.models import User
from orders.models import Order
from .models import Restaurant, RestaurantCategory, Menu, Product, WorkingHours


# ─────────────────────────────────────────────
# دالة مساعدة: بناء بيانات المطعم الكاملة للقوائم
# ─────────────────────────────────────────────
def _restaurant_list_data(r, request):
    total_orders = Order.objects.filter(restaurant=r, status="delivered").count()
    cat = None
    if r.category:
        cat = {
            "id":    r.category.id,
            "name":  r.category.name,
            "image": request.build_absolute_uri(r.category.image.url)
                     if r.category.image else None,
        }
    rating_val = float(r.rating)
    return {
        "id":                r.id,
        "name":              r.name,
        "restaurant_name":   r.name,
        "owner_name":        r.owner_name,
        "address":           r.address,
        "city":              r.city,
        "lat":               r.lat,
        "lng":               r.lng,
        "rating":            rating_val,
        "avg_rating":        rating_val,
        "is_open":           r.is_open,
        "logo":              request.build_absolute_uri(r.logo.url) if r.logo else None,
        "cover_image":       request.build_absolute_uri(r.cover_image.url)
                             if r.cover_image else None,
        "total_orders":      total_orders,
        "likes":             0,
        "total_likes":       0,
        "delivery_fee":      50,
        "estimated_minutes": 30,
        "category":          cat,
        "category_id":       r.category_id,
    }


# ─────────────────────────────────────────────
# تصنيفات المطاعم
# GET /api/restaurants/categories/
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([AllowAny])
def categories_list(request):
    categories = RestaurantCategory.objects.all()
    data = [
        {
            "id":    c.id,
            "name":  c.name,
            "image": request.build_absolute_uri(c.image.url) if c.image else None,
        }
        for c in categories
    ]
    return Response(data)


# ─────────────────────────────────────────────
# قائمة المطاعم المتاحة للعملاء
# GET /api/restaurants/
# GET /api/restaurants/?category_id=<id>
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([AllowAny])
def restaurants_list(request):
    qs = Restaurant.objects.filter(approval_status="approved").select_related("category")
    category_id = request.query_params.get("category_id")
    if category_id:
        qs = qs.filter(category_id=category_id)
    data = [_restaurant_list_data(r, request) for r in qs]
    return Response(data)


# ─────────────────────────────────────────────
# تفاصيل مطعم واحد مع قوائمه ومنتجاته
# GET /api/restaurants/<id>/
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([AllowAny])
def restaurant_detail(request, pk):
    r = get_object_or_404(
        Restaurant.objects.select_related("category"),
        pk=pk, approval_status="approved"
    )
    menus = []
    for menu in r.menus.filter(is_active=True):
        products = [
            {
                "id":               p.id,
                "name":             p.name,
                "description":      p.description,
                "price":            float(p.price),
                "final_price":      float(p.final_price),
                "discount_percent": p.discount_percent,
                "display_type":     p.display_type,
                "is_available":     p.is_available,
                "image":            request.build_absolute_uri(p.image.url) if p.image else None,
            }
            for p in menu.products.filter(is_available=True)
        ]
        menus.append({
            "id":         menu.id,
            "name":       menu.name,
            "time_label": menu.time_label,
            "products":   products,
        })
    working_hours = [
        {
            "day":        wh.day,
            "open_time":  str(wh.open_time),
            "close_time": str(wh.close_time),
            "is_active":  wh.is_active,
        }
        for wh in r.working_hours.all()
    ]
    total_orders = Order.objects.filter(restaurant=r, status="delivered").count()
    rating_val   = float(r.rating)
    cat = None
    if r.category:
        cat = {
            "id":    r.category.id,
            "name":  r.category.name,
            "image": request.build_absolute_uri(r.category.image.url)
                     if r.category.image else None,
        }
    return Response({
        "id":                r.id,
        "name":              r.name,
        "restaurant_name":   r.name,
        "owner_name":        r.owner_name,
        "address":           r.address,
        "city":              r.city,
        "lat":               r.lat,
        "lng":               r.lng,
        "rating":            rating_val,
        "avg_rating":        rating_val,
        "is_open":           r.is_open,
        "logo":              request.build_absolute_uri(r.logo.url) if r.logo else None,
        "cover_image":       request.build_absolute_uri(r.cover_image.url)
                             if r.cover_image else None,
        "total_orders":      total_orders,
        "likes":             0,
        "total_likes":       0,
        "delivery_fee":      50,
        "estimated_minutes": 30,
        "category":          cat,
        "category_id":       r.category_id,
        "menus":             menus,
        "working_hours":     working_hours,
    })


# ─────────────────────────────────────────────
# بيانات المطعم الخاص بالمالك (لوحة التحكم)
# GET /api/restaurants/mine/
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_restaurant(request):
    if request.user.role != User.Role.RESTAURANT:
        return Response({"detail": "غير مصرح."}, status=403)
    r = get_object_or_404(Restaurant, owner=request.user)
    total_orders = Order.objects.filter(restaurant=r, status="delivered").count()
    rating_val   = float(r.rating)
    return Response({
        "id":              r.id,
        "name":            r.name,
        "restaurant_name": r.name,
        "owner_name":      r.owner_name,
        "address":         r.address,
        "city":            r.city,
        "lat":             r.lat,
        "lng":             r.lng,
        "rating":          rating_val,
        "avg_rating":      rating_val,
        "is_open":         r.is_open,
        "approval_status": r.approval_status,
        "logo":            request.build_absolute_uri(r.logo.url) if r.logo else None,
        "cover_image":     request.build_absolute_uri(r.cover_image.url)
                           if r.cover_image else None,
        "total_orders":    total_orders,
        "likes":           0,
        "total_likes":     0,
        "delivery_fee":    50,
        "estimated_minutes": 30,
    })


# ─────────────────────────────────────────────
# تحديث حالة المطعم (مفتوح/مغلق)
# PATCH /api/restaurants/mine/toggle-open/
# ─────────────────────────────────────────────
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def toggle_restaurant_open(request):
    if request.user.role != User.Role.RESTAURANT:
        return Response({"detail": "غير مصرح."}, status=403)
    r = get_object_or_404(Restaurant, owner=request.user)
    r.is_open = not r.is_open
    r.save(update_fields=["is_open"])
    return Response({"is_open": r.is_open})


# ─────────────────────────────────────────────
# إنشاء قائمة جديدة
# POST /api/restaurants/menus/
# ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_menu(request):
    if request.user.role != User.Role.RESTAURANT:
        return Response({"detail": "غير مصرح."}, status=403)
    r = get_object_or_404(Restaurant, owner=request.user)
    name = request.data.get("name", "").strip()
    if not name:
        return Response({"detail": "اسم القائمة مطلوب."}, status=400)
    menu = Menu.objects.create(
        restaurant=r,
        name=name,
        time_label=request.data.get("time_label", ""),
    )
    return Response({"id": menu.id, "name": menu.name}, status=201)


# ─────────────────────────────────────────────
# إضافة منتج لقائمة
# POST /api/restaurants/products/
# ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_product(request):
    if request.user.role != User.Role.RESTAURANT:
        return Response({"detail": "غير مصرح."}, status=403)
    menu_id = request.data.get("menu_id")
    menu = get_object_or_404(Menu, pk=menu_id, restaurant__owner=request.user)
    name  = request.data.get("name", "").strip()
    price = request.data.get("price")
    if not name or not price:
        return Response({"detail": "الاسم والسعر مطلوبان."}, status=400)
    product = Product.objects.create(
        menu=menu,
        name=name,
        description=request.data.get("description", ""),
        price=price,
        display_type=request.data.get("display_type", "normal"),
        discount_percent=request.data.get("discount_percent", 0),
        image=request.FILES.get("image"),
    )
    return Response({
        "id":          product.id,
        "name":        product.name,
        "price":       float(product.price),
        "final_price": float(product.final_price),
        "image":       request.build_absolute_uri(product.image.url) if product.image else None,
    }, status=201)


# ─────────────────────────────────────────────
# تعديل منتج
# PATCH /api/restaurants/products/<id>/
# ─────────────────────────────────────────────
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_product(request, pk):
    if request.user.role != User.Role.RESTAURANT:
        return Response({"detail": "غير مصرح."}, status=403)
    product = get_object_or_404(Product, pk=pk, menu__restaurant__owner=request.user)
    for field in ["name", "description", "price", "display_type", "discount_percent", "is_available"]:
        if field in request.data:
            setattr(product, field, request.data[field])
    if "image" in request.FILES:
        product.image = request.FILES["image"]
    product.save()
    return Response({
        "id":          product.id,
        "name":        product.name,
        "final_price": float(product.final_price),
        "image":       request.build_absolute_uri(product.image.url) if product.image else None,
    })


# ─────────────────────────────────────────────
# حذف منتج
# DELETE /api/restaurants/products/<id>/delete/
# ─────────────────────────────────────────────
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_product(request, pk):
    if request.user.role != User.Role.RESTAURANT:
        return Response({"detail": "غير مصرح."}, status=403)
    product = get_object_or_404(Product, pk=pk, menu__restaurant__owner=request.user)
    product.delete()
    return Response(status=204)


# ─────────────────────────────────────────────
# قائمة العروض الترويجية (المنتجات المخفَّضة)
# GET /api/promotions/
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([AllowAny])
def promotions(request):
    products = Product.objects.filter(
        is_available=True,
        discount_percent__gt=0,
        menu__restaurant__approval_status="approved",
    ).select_related("menu__restaurant")

    data = []
    for p in products:
        r          = p.menu.restaurant
        orig_price = float(p.price)
        disc       = p.discount_percent or 0
        data.append({
            "id":               p.id,
            "name":             p.name,
            "description":      p.description or "",
            "image":            request.build_absolute_uri(p.image.url) if p.image else "",
            "price":            orig_price,
            "discounted_price": round(orig_price * (1 - disc / 100), 2),
            "discount_percent": disc,
            "display_type":     p.display_type,
            "menu_name":        p.menu.name,
            "restaurant": {
                "id":   r.id,
                "name": r.name,
                "logo": request.build_absolute_uri(r.logo.url) if r.logo else "",
            },
        })

    return Response(data)


# ─────────────────────────────────────────────
# تفاصيل منتج/عرض ترويجي
# GET /api/promotions/<pk>/
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([AllowAny])
def promotion_detail(request, pk):
    p = get_object_or_404(
        Product,
        pk=pk,
        is_available=True,
        menu__restaurant__approval_status="approved",
    )
    r          = p.menu.restaurant
    orig_price = float(p.price)
    disc       = p.discount_percent or 0
    return Response({
        "id":               p.id,
        "name":             p.name,
        "description":      p.description or "",
        "image":            request.build_absolute_uri(p.image.url) if p.image else "",
        "price":            orig_price,
        "discounted_price": round(orig_price * (1 - disc / 100), 2),
        "discount_percent": disc,
        "display_type":     p.display_type,
        "menu_name":        p.menu.name,
        "restaurant": {
            "id":   r.id,
            "name": r.name,
            "logo": request.build_absolute_uri(r.logo.url) if r.logo else "",
        },
    })
