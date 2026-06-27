"""
restaurants/api.py — API المطاعم والقوائم والمنتجات
"""
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from accounts.models import User
from orders.models import Order
from .models import Restaurant, RestaurantCategory, Menu, Product, WorkingHours


# ─────────────────────────────────────────────
# دالة مساعدة: بناء رابط الصورة
# ✅ تتعامل مع 3 حالات:
#    1. Cloudinary URL كامل → يُرجع مباشرة
#    2. مسار محلي قديم     → يُرجع "" بدل 404
#    3. حقل فارغ           → يُرجع ""
# ─────────────────────────────────────────────
def _image_url(image_field, request=None):
    if not image_field:
        return ""
    try:
        # CloudinaryField يُرجع الـ URL مباشرة عبر str()
        url = str(image_field)
        if url.startswith("http://") or url.startswith("https://"):
            return url
        # محاولة .url للتوافق مع ImageField القديم
        url = image_field.url
        if url.startswith("http://") or url.startswith("https://"):
            return url
    except Exception:
        pass
    return ""


# ─────────────────────────────────────────────
# دالة مساعدة: بناء بيانات المطعم للقوائم
# ─────────────────────────────────────────────
def _restaurant_list_data(r, request):
    total_orders = Order.objects.filter(restaurant=r, status="delivered").count()
    cat = None
    if r.category:
        cat = {
            "id":    r.category.id,
            "name":  r.category.name,
            "image": _image_url(r.category.image, request),
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
        "logo":              _image_url(r.logo, request),
        "cover_image":       _image_url(r.cover_image, request),
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
            "image": _image_url(c.image, request),
        }
        for c in categories
    ]
    return Response(data)


# ─────────────────────────────────────────────
# قائمة المطاعم
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
                "image":            _image_url(p.image, request),
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
            "image": _image_url(r.category.image, request),
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
        "logo":              _image_url(r.logo, request),
        "cover_image":       _image_url(r.cover_image, request),
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
# بيانات المطعم الخاص بالمالك
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
        "approval_status":   r.approval_status,
        "logo":              _image_url(r.logo, request),
        "cover_image":       _image_url(r.cover_image, request),
        "total_orders":      total_orders,
        "likes":             0,
        "total_likes":       0,
        "delivery_fee":      50,
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
# رفع لوجو المطعم وصورة الغلاف
# PATCH /api/restaurants/mine/images/
# form-data: logo (file, اختياري), cover_image (file, اختياري)
# ─────────────────────────────────────────────
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_restaurant_images(request):
    if request.user.role != User.Role.RESTAURANT:
        return Response({"detail": "غير مصرح."}, status=403)

    r = get_object_or_404(Restaurant, owner=request.user)

    updated = []

    if "logo" in request.FILES:
        r.logo = request.FILES["logo"]
        updated.append("logo")

    if "cover_image" in request.FILES:
        r.cover_image = request.FILES["cover_image"]
        updated.append("cover_image")

    if not updated:
        return Response(
            {"detail": "لم يتم إرسال أي صورة. أرسل logo أو cover_image أو كليهما."},
            status=400,
        )

    r.save(update_fields=updated)

    return Response({
        "detail":      f"تم تحديث: {', '.join(updated)}",
        "logo":        _image_url(r.logo, request),
        "cover_image": _image_url(r.cover_image, request),
    })


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
# تعديل قائمة
# PATCH /api/restaurants/menus/<id>/
# ─────────────────────────────────────────────
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_menu(request, pk):
    if request.user.role != User.Role.RESTAURANT:
        return Response({"detail": "غير مصرح."}, status=403)
    menu = get_object_or_404(Menu, pk=pk, restaurant__owner=request.user)
    updated = []
    if "name" in request.data:
        name = request.data["name"].strip()
        if not name:
            return Response({"detail": "اسم القائمة لا يمكن أن يكون فارغاً."}, status=400)
        menu.name = name
        updated.append("name")
    if "time_label" in request.data:
        menu.time_label = request.data["time_label"]
        updated.append("time_label")
    if updated:
        menu.save(update_fields=updated)
    return Response({"id": menu.id, "name": menu.name, "time_label": menu.time_label})


# ─────────────────────────────────────────────
# حذف قائمة
# DELETE /api/restaurants/menus/<id>/
# ─────────────────────────────────────────────
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_menu(request, pk):
    if request.user.role != User.Role.RESTAURANT:
        return Response({"detail": "غير مصرح."}, status=403)
    menu = get_object_or_404(Menu, pk=pk, restaurant__owner=request.user)
    menu.delete()
    return Response(status=204)


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
    menu    = get_object_or_404(Menu, pk=menu_id, restaurant__owner=request.user)
    name    = request.data.get("name", "").strip()
    price   = request.data.get("price")
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
        "image":       _image_url(product.image, request),
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
        "image":       _image_url(product.image, request),
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
# قائمة العروض الترويجية
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
            "image":            _image_url(p.image, request),
            "price":            orig_price,
            "discounted_price": round(orig_price * (1 - disc / 100), 2),
            "discount_percent": disc,
            "display_type":     p.display_type,
            "menu_name":        p.menu.name,
            "restaurant": {
                "id":   r.id,
                "name": r.name,
                "logo": _image_url(r.logo, request),
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
        "image":            _image_url(p.image, request),
        "price":            orig_price,
        "discounted_price": round(orig_price * (1 - disc / 100), 2),
        "discount_percent": disc,
        "display_type":     p.display_type,
        "menu_name":        p.menu.name,
        "restaurant": {
            "id":   r.id,
            "name": r.name,
            "logo": _image_url(r.logo, request),
        },
    })


# ─────────────────────────────────────────────
# ⚠️  endpoint مؤقت — يمسح مسارات الصور المكسورة (المحلية)
# GET /api/restaurants/clear-broken-images/
# احذفه بعد الانتهاء
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([AllowAny])
def clear_broken_images(request):
    cleared = []
    for p in Product.objects.exclude(image="").exclude(image=None):
        url = str(p.image)
        if not url.startswith("http"):
            cleared.append({"id": p.id, "name": p.name, "old_path": url})
            p.image = ""
            p.save(update_fields=["image"])
    return Response({"cleared": len(cleared), "details": cleared})


# ─────────────────────────────────────────────
# ⚠️  endpoint مؤقت لاختبار Cloudinary وترحيل الصور
# GET /api/restaurants/migrate-images/
# احذفه بعد التأكد من عمل كل شيء
# ─────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([AllowAny])
def migrate_images(request):
    import cloudinary.uploader
    import os

    # ── اختبار المتغيرات ──
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key    = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')

    if not all([cloud_name, api_key, api_secret]):
        return Response({
            "error":      "متغيرات Cloudinary مفقودة",
            "cloud_name": cloud_name or "❌ مفقود",
            "api_key":    api_key    or "❌ مفقود",
            "api_secret": "✅ موجود" if api_secret else "❌ مفقود",
        }, status=500)

    results = {"success": [], "failed": [], "skipped": []}

    for p in Product.objects.exclude(image="").exclude(image=None):
        url = str(p.image)
        if url.startswith("http"):
            results["skipped"].append({"id": p.id, "name": p.name, "url": url})
            continue
        try:
            full_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "media", url
            )
            result = cloudinary.uploader.upload(
                full_path,
                public_id=f"wassel/products/{p.id}",
                overwrite=True,
            )
            p.image = result["secure_url"]
            p.save(update_fields=["image"])
            results["success"].append({"id": p.id, "name": p.name, "url": result["secure_url"]})
        except Exception as e:
            results["failed"].append({"id": p.id, "name": p.name, "error": str(e)})

    return Response({
        "cloudinary": f"✅ {cloud_name}",
        "migrated":   len(results["success"]),
        "skipped":    len(results["skipped"]),
        "failed":     len(results["failed"]),
        "details":    results,
    })
