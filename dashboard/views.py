from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta

from accounts.models import User, LivreurProfile, ClientProfile
from restaurants.models import Restaurant, RestaurantCategory, Menu, Product
from orders.models import Order

from .decorators import admin_required


def sidebar_counts():
    """أعداد العناصر بانتظار المراجعة، تُعرض كشارة في الشريط الجانبي."""
    return {
        "pending_restaurants_count": Restaurant.objects.filter(
            approval_status=Restaurant.ApprovalStatus.PENDING
        ).count(),
        "pending_livreurs_count": LivreurProfile.objects.filter(
            approval_status=LivreurProfile.ApprovalStatus.PENDING
        ).count(),
    }


# ===== تسجيل الدخول / الخروج =====

def login_view(request):
    if request.user.is_authenticated and getattr(request.user, "role", None) == "admin":
        return redirect("dashboard:home")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and getattr(user, "role", None) == "admin":
            login(request, user)
            return redirect("dashboard:home")
        elif user is not None:
            error = "هذا الحساب ليس حساب أدمن."
        else:
            error = "اسم المستخدم أو كلمة المرور غير صحيحة."

    return render(request, "dashboard/login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("dashboard:login")


# ===== الرئيسية =====

@admin_required
def home(request):
    today = timezone.now().date()
    last_7_days = timezone.now() - timedelta(days=7)

    context = {
        "active": "home",
        "total_restaurants": Restaurant.objects.count(),
        "total_livreurs": LivreurProfile.objects.count(),
        "total_clients": ClientProfile.objects.count(),
        "total_orders": Order.objects.count(),
        "orders_today": Order.objects.filter(created_at__date=today).count(),
        "orders_last_7_days": Order.objects.filter(created_at__gte=last_7_days).count(),
        "pending_restaurants": Restaurant.objects.filter(
            approval_status=Restaurant.ApprovalStatus.PENDING
        ).count(),
        "pending_livreurs": LivreurProfile.objects.filter(
            approval_status=LivreurProfile.ApprovalStatus.PENDING
        ).count(),
        "recent_orders": Order.objects.select_related("client", "restaurant").order_by("-created_at")[:10],
        **sidebar_counts(),
    }
    return render(request, "dashboard/home.html", context)


# ===== المطاعم =====

@admin_required
def restaurants_list(request):
    status = request.GET.get("status", "all")
    qs = Restaurant.objects.select_related("owner", "category").order_by("-created_at")
    if status in ("pending", "approved", "rejected"):
        qs = qs.filter(approval_status=status)

    context = {
        "active": "restaurants",
        "restaurants": qs,
        "current_status": status,
        **sidebar_counts(),
    }
    return render(request, "dashboard/restaurants_list.html", context)


@admin_required
def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant.objects.select_related("owner", "category"), pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            restaurant.approval_status = Restaurant.ApprovalStatus.APPROVED
            restaurant.save()
            messages.success(request, f"تمت الموافقة على مطعم «{restaurant.name}».")
        elif action == "reject":
            restaurant.approval_status = Restaurant.ApprovalStatus.REJECTED
            restaurant.save()
            messages.success(request, f"تم رفض مطعم «{restaurant.name}».")
        return redirect("dashboard:restaurant_detail", pk=pk)

    context = {
        "active": "restaurants",
        "restaurant": restaurant,
        "menus": restaurant.menus.prefetch_related("products"),
        **sidebar_counts(),
    }
    return render(request, "dashboard/restaurant_detail.html", context)


@admin_required
def restaurant_create(request):
    categories = RestaurantCategory.objects.all()

    if request.method == "POST":
        phone = request.POST.get("phone", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        password = request.POST.get("password", "").strip()
        name = request.POST.get("name", "").strip()
        owner_name = request.POST.get("owner_name", "").strip()
        category_id = request.POST.get("category") or None
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        bank_account = request.POST.get("bank_account", "").strip()
        auto_approve = request.POST.get("auto_approve") == "on"

        errors = []
        if not phone:
            errors.append("رقم الهاتف إلزامي.")
        elif User.objects.filter(phone=phone).exists():
            errors.append("رقم الهاتف هذا مستخدم بالفعل.")
        if not password or len(password) < 4:
            errors.append("كلمة المرور يجب أن تكون 4 أحرف على الأقل.")
        if not name:
            errors.append("اسم المطعم إلزامي.")
        if not owner_name:
            errors.append("اسم المالك إلزامي.")
        if not address:
            errors.append("العنوان إلزامي.")
        if not city:
            errors.append("المدينة إلزامية.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            owner = User(role=User.Role.RESTAURANT, phone=phone, full_name=full_name or owner_name)
            owner.set_password(password)
            owner.save()

            restaurant = Restaurant.objects.create(
                owner=owner,
                name=name,
                owner_name=owner_name,
                category_id=category_id,
                address=address,
                city=city,
                bank_account=bank_account,
                approval_status=(
                    Restaurant.ApprovalStatus.APPROVED if auto_approve
                    else Restaurant.ApprovalStatus.PENDING
                ),
            )
            messages.success(request, f"تمت إضافة مطعم «{restaurant.name}» بنجاح.")
            return redirect("dashboard:restaurant_detail", pk=restaurant.pk)

    context = {
        "active": "restaurants",
        "categories": categories,
        **sidebar_counts(),
    }
    return render(request, "dashboard/restaurant_form.html", context)


@admin_required
def product_create(request, restaurant_pk):
    restaurant = get_object_or_404(Restaurant, pk=restaurant_pk)
    menus = restaurant.menus.all()

    if request.method == "POST":
        menu_choice = request.POST.get("menu", "")
        new_menu_name = request.POST.get("new_menu_name", "").strip()

        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        price_raw = request.POST.get("price", "").strip()
        display_type = request.POST.get("display_type", Product.DisplayType.NORMAL)
        discount_raw = request.POST.get("discount_percent", "0").strip() or "0"
        is_available = request.POST.get("is_available") == "on"
        image = request.FILES.get("image")

        errors = []
        if not name:
            errors.append("اسم المنتج إلزامي.")

        price_value = None
        try:
            price_value = Decimal(price_raw)
            if price_value <= 0:
                errors.append("السعر يجب أن يكون أكبر من صفر.")
        except (InvalidOperation, ValueError):
            errors.append("السعر غير صالح.")

        try:
            discount_value = int(discount_raw)
        except ValueError:
            discount_value = 0
        if display_type == Product.DisplayType.DISCOUNT and not (0 < discount_value <= 100):
            errors.append("نسبة الخصم يجب أن تكون بين 1 و100.")

        menu = None
        if not menus.exists() or menu_choice == "new":
            menu_name = new_menu_name or "القائمة الرئيسية"
        else:
            menu = menus.filter(pk=menu_choice).first()
            if menu is None:
                errors.append("القائمة المختارة غير صالحة.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            if menu is None:
                menu, _ = Menu.objects.get_or_create(restaurant=restaurant, name=menu_name)
            Product.objects.create(
                menu=menu,
                name=name,
                description=description,
                price=price_value,
                image=image,
                display_type=display_type,
                discount_percent=discount_value if display_type == Product.DisplayType.DISCOUNT else 0,
                is_available=is_available,
            )
            messages.success(request, f"تمت إضافة المنتج «{name}» إلى «{restaurant.name}» بنجاح.")
            return redirect("dashboard:restaurant_detail", pk=restaurant.pk)

    context = {
        "active": "restaurants",
        "restaurant": restaurant,
        "menus": menus,
        "display_type_choices": Product.DisplayType.choices,
        **sidebar_counts(),
    }
    return render(request, "dashboard/product_form.html", context)


# ===== المناديب =====

@admin_required
def livreurs_list(request):
    status = request.GET.get("status", "all")
    qs = LivreurProfile.objects.select_related("user").order_by("-created_at")
    if status in ("pending", "approved", "rejected"):
        qs = qs.filter(approval_status=status)

    context = {
        "active": "livreurs",
        "livreurs": qs,
        "current_status": status,
        **sidebar_counts(),
    }
    return render(request, "dashboard/livreurs_list.html", context)


@admin_required
def livreur_detail(request, pk):
    livreur = get_object_or_404(LivreurProfile.objects.select_related("user"), pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            livreur.approval_status = LivreurProfile.ApprovalStatus.APPROVED
            livreur.save()
            messages.success(request, f"تمت الموافقة على المندوب «{livreur.user.full_name}».")
        elif action == "reject":
            livreur.approval_status = LivreurProfile.ApprovalStatus.REJECTED
            livreur.save()
            messages.success(request, f"تم رفض المندوب «{livreur.user.full_name}».")
        return redirect("dashboard:livreur_detail", pk=pk)

    context = {
        "active": "livreurs",
        "livreur": livreur,
        "deliveries": livreur.user.deliveries.select_related("client", "restaurant").order_by("-created_at")[:20],
        **sidebar_counts(),
    }
    return render(request, "dashboard/livreur_detail.html", context)


@admin_required
def livreur_create(request):
    if request.method == "POST":
        phone = request.POST.get("phone", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        password = request.POST.get("password", "").strip()
        address = request.POST.get("address", "").strip()
        vehicle_plate = request.POST.get("vehicle_plate", "").strip()
        vehicle_model = request.POST.get("vehicle_model", "").strip()
        bank_account = request.POST.get("bank_account", "").strip()
        auto_approve = request.POST.get("auto_approve") == "on"
        id_document = request.FILES.get("id_document")
        license_document = request.FILES.get("license_document")

        errors = []
        if not phone:
            errors.append("رقم الهاتف إلزامي.")
        elif User.objects.filter(phone=phone).exists():
            errors.append("رقم الهاتف هذا مستخدم بالفعل.")
        if not full_name:
            errors.append("اسم المندوب إلزامي.")
        if not password or len(password) < 4:
            errors.append("كلمة المرور يجب أن تكون 4 أحرف على الأقل.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            user = User(role=User.Role.LIVREUR, phone=phone, full_name=full_name)
            user.set_password(password)
            user.save()

            livreur = LivreurProfile.objects.create(
                user=user,
                address=address,
                vehicle_plate=vehicle_plate,
                vehicle_model=vehicle_model,
                bank_account=bank_account,
                id_document=id_document,
                license_document=license_document,
                approval_status=(
                    LivreurProfile.ApprovalStatus.APPROVED if auto_approve
                    else LivreurProfile.ApprovalStatus.PENDING
                ),
            )
            messages.success(request, f"تمت إضافة المندوب «{user.full_name}» بنجاح.")
            return redirect("dashboard:livreur_detail", pk=livreur.pk)

    context = {
        "active": "livreurs",
        **sidebar_counts(),
    }
    return render(request, "dashboard/livreur_form.html", context)


# ===== الطلبات =====

@admin_required
def orders_list(request):
    status = request.GET.get("status", "all")
    order_type = request.GET.get("type", "all")
    qs = Order.objects.select_related("client", "restaurant", "livreur").order_by("-created_at")
    if status != "all":
        qs = qs.filter(status=status)
    if order_type != "all":
        qs = qs.filter(order_type=order_type)

    context = {
        "active": "orders",
        "orders": qs[:200],
        "current_status": status,
        "current_type": order_type,
        "status_choices": Order.Status.choices,
        **sidebar_counts(),
    }
    return render(request, "dashboard/orders_list.html", context)


@admin_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("client", "restaurant", "livreur"), pk=pk
    )
    context = {
        "active": "orders",
        "order": order,
        "items": order.items.select_related("product"),
        "history": order.status_history.order_by("timestamp"),
        **sidebar_counts(),
    }
    return render(request, "dashboard/order_detail.html", context)


# ===== العملاء =====

@admin_required
def clients_list(request):
    qs = ClientProfile.objects.select_related("user").order_by("-user__date_joined")
    context = {
        "active": "clients",
        "clients": qs,
        **sidebar_counts(),
    }
    return render(request, "dashboard/clients_list.html", context)


# ===== الفئات =====

@admin_required
def categories_list(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            RestaurantCategory.objects.get_or_create(name=name)
            messages.success(request, "تمت إضافة الفئة بنجاح.")
        return redirect("dashboard:categories")

    context = {
        "active": "categories",
        "categories": RestaurantCategory.objects.all(),
        **sidebar_counts(),
    }
    return render(request, "dashboard/categories_list.html", context)


@admin_required
def category_delete(request, pk):
    category = get_object_or_404(RestaurantCategory, pk=pk)
    if request.method == "POST":
        category.delete()
        messages.success(request, "تم حذف الفئة.")
    return redirect("dashboard:categories")
