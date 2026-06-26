"""
accounts/api.py — REST API لتسجيل الدخول وإنشاء الحسابات
"""
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import User, ClientProfile, LivreurProfile


# ─────────────────────────────────────────────
# تسجيل الدخول (جميع الأدوار)
# POST /api/auth/login/
# ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    phone    = request.data.get("phone", "").strip()
    password = request.data.get("password", "").strip()

    if not phone or not password:
        return Response({"detail": "الهاتف وكلمة المرور مطلوبان."}, status=400)

    user = authenticate(request, username=phone, password=password)
    if user is None:
        return Response({"detail": "بيانات الدخول غير صحيحة."}, status=401)

    token, _ = Token.objects.get_or_create(user=user)

    payload = {
        "token": token.key,
        "role":  user.role,
        "user": {
            "id":        user.id,
            "full_name": user.full_name,
            "phone":     user.phone,
        },
    }

    if user.role == User.Role.RESTAURANT and hasattr(user, "restaurant"):
        r = user.restaurant
        payload["restaurant"] = {
            "id":              r.id,
            "name":            r.name,
            "approval_status": r.approval_status,
            "is_open":         r.is_open,
        }
    elif user.role == User.Role.LIVREUR and hasattr(user, "livreur_profile"):
        lp = user.livreur_profile
        payload["livreur"] = {
            "id":              lp.id,
            "approval_status": lp.approval_status,
            "is_online":       lp.is_online,
        }

    return Response(payload)


# ─────────────────────────────────────────────
# تسجيل عميل جديد (بدون كلمة مرور)
# POST /api/auth/register/client/
# ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([AllowAny])
def register_client(request):
    full_name = request.data.get("full_name", "").strip()
    phone     = request.data.get("phone", "").strip()
    address   = request.data.get("address", "").strip()
    lat       = request.data.get("lat")
    lng       = request.data.get("lng")

    if not full_name or not phone:
        return Response({"detail": "الاسم ورقم الهاتف مطلوبان."}, status=400)

    if User.objects.filter(phone=phone).exists():
        return Response({"detail": "رقم الهاتف مسجّل مسبقاً."}, status=409)

    user = User(role=User.Role.CLIENT, phone=phone, full_name=full_name)
    user.set_unusable_password()
    user.save()

    ClientProfile.objects.create(
        user=user,
        default_address=address,
        default_lat=lat,
        default_lng=lng,
    )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        "token": token.key,
        "role":  user.role,
        "user":  {"id": user.id, "full_name": user.full_name, "phone": user.phone},
    }, status=201)


# ─────────────────────────────────────────────
# تسجيل مطعم جديد
# POST /api/auth/register/restaurant/
# ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([AllowAny])
def register_restaurant(request):
    required = ["full_name", "phone", "password", "restaurant_name",
                "owner_name", "address", "city"]
    for field in required:
        if not request.data.get(field, "").strip():
            return Response({"detail": f"الحقل '{field}' مطلوب."}, status=400)

    phone = request.data.get("phone").strip()
    if User.objects.filter(phone=phone).exists():
        return Response({"detail": "رقم الهاتف مسجّل مسبقاً."}, status=409)

    user = User(role=User.Role.RESTAURANT, phone=phone,
                full_name=request.data["full_name"].strip())
    user.set_password(request.data["password"])
    user.save()

    from restaurants.models import Restaurant, RestaurantCategory
    category_id = request.data.get("category_id")
    category = None
    if category_id:
        category = RestaurantCategory.objects.filter(pk=category_id).first()

    Restaurant.objects.create(
        owner=user,
        name=request.data["restaurant_name"].strip(),
        owner_name=request.data["owner_name"].strip(),
        category=category,
        address=request.data["address"].strip(),
        city=request.data["city"].strip(),
        lat=request.data.get("lat"),
        lng=request.data.get("lng"),
        bank_account=request.data.get("bank_account", ""),
        logo=request.FILES.get("logo"),
        cover_image=request.FILES.get("cover_image"),
        approval_status="pending",
    )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        "token":           token.key,
        "role":            user.role,
        "user":            {"id": user.id, "full_name": user.full_name, "phone": user.phone},
        "approval_status": "pending",
    }, status=201)


# ─────────────────────────────────────────────
# تسجيل مندوب توصيل
# POST /api/auth/register/livreur/
# ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([AllowAny])
def register_livreur(request):
    required = ["full_name", "phone", "password"]
    for field in required:
        if not request.data.get(field, "").strip():
            return Response({"detail": f"الحقل '{field}' مطلوب."}, status=400)

    phone = request.data.get("phone").strip()
    if User.objects.filter(phone=phone).exists():
        return Response({"detail": "رقم الهاتف مسجّل مسبقاً."}, status=409)

    user = User(role=User.Role.LIVREUR, phone=phone,
                full_name=request.data["full_name"].strip())
    user.set_password(request.data["password"])
    user.save()

    LivreurProfile.objects.create(
        user=user,
        address=request.data.get("address", ""),
        vehicle_plate=request.data.get("vehicle_plate", ""),
        vehicle_model=request.data.get("vehicle_model", ""),
        bank_account=request.data.get("bank_account", ""),
        id_document=request.FILES.get("id_document"),
        license_document=request.FILES.get("license_document"),
        approval_status="pending",
    )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        "token":           token.key,
        "role":            user.role,
        "user":            {"id": user.id, "full_name": user.full_name, "phone": user.phone},
        "approval_status": "pending",
    }, status=201)


# ─────────────────────────────────────────────
# تسجيل الخروج
# POST /api/auth/logout/
# ─────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.auth.delete()
    return Response({"detail": "تم تسجيل الخروج."})


# ─────────────────────────────────────────────
# بيانات الحساب الحالي + تعديله
# GET  /api/auth/me/  → جلب البيانات
# PATCH /api/auth/me/ → تعديل الاسم والعنوان والصورة
# ─────────────────────────────────────────────
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user

    # ── GET ──────────────────────────────────
    if request.method == "GET":
        data = {
            "id":        user.id,
            "full_name": user.full_name,
            "phone":     user.phone,
            "role":      user.role,
            "address":   getattr(user, "address", "") or "",
        }
        # بيانات إضافية حسب الدور
        if user.role == User.Role.LIVREUR and hasattr(user, "livreur_profile"):
            lp = user.livreur_profile
            data["is_online"]       = lp.is_online
            data["approval_status"] = lp.approval_status
        elif user.role == User.Role.RESTAURANT and hasattr(user, "restaurant"):
            r = user.restaurant
            data["restaurant_id"]   = r.id
            data["restaurant_name"] = r.name
            data["approval_status"] = r.approval_status
        return Response(data)

    # ── PATCH ─────────────────────────────────
    full_name = request.data.get("full_name")
    address   = request.data.get("address")
    lat       = request.data.get("lat")
    lng       = request.data.get("lng")

    updated_fields = []

    if full_name is not None:
        full_name = full_name.strip()
        if not full_name:
            return Response({"detail": "الاسم لا يمكن أن يكون فارغاً."}, status=400)
        user.full_name = full_name
        updated_fields.append("full_name")

    if address is not None:
        user.address = address.strip()
        updated_fields.append("address")

    if lat is not None:
        try:
            user.lat = float(lat)
            updated_fields.append("lat")
        except (TypeError, ValueError):
            return Response({"detail": "lat يجب أن يكون رقماً."}, status=400)

    if lng is not None:
        try:
            user.lng = float(lng)
            updated_fields.append("lng")
        except (TypeError, ValueError):
            return Response({"detail": "lng يجب أن يكون رقماً."}, status=400)

    # رفع الصورة الشخصية (multipart)
    if "avatar" in request.FILES:
        user.avatar = request.FILES["avatar"]
        updated_fields.append("avatar")

    if updated_fields:
        user.save(update_fields=updated_fields)

    return Response({
        "id":        user.id,
        "full_name": user.full_name,
        "phone":     user.phone,
        "role":      user.role,
        "address":   getattr(user, "address", "") or "",
    })
