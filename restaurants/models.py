from decimal import Decimal

from django.db import models
from accounts.models import User
from cloudinary.models import CloudinaryField


# ══════════════════════════════════════════
#  فئة المطعم
# ══════════════════════════════════════════
class RestaurantCategory(models.Model):
    name  = models.CharField(max_length=100, unique=True)
    image = CloudinaryField("category_images", null=True, blank=True)

    class Meta:
        verbose_name        = "فئة مطعم"
        verbose_name_plural = "فئات المطاعم"

    def __str__(self):
        return self.name


# ══════════════════════════════════════════
#  المطعم
# ══════════════════════════════════════════
class Restaurant(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING  = "pending",  "قيد المراجعة"
        APPROVED = "approved", "موافق عليه"
        REJECTED = "rejected", "مرفوض"

    owner = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="restaurant"
    )
    name       = models.CharField(max_length=150)
    owner_name = models.CharField(max_length=150)
    category   = models.ForeignKey(
        RestaurantCategory,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="restaurants",
    )

    address      = models.CharField(max_length=255)
    city         = models.CharField(max_length=100)
    lat          = models.FloatField(null=True, blank=True)
    lng          = models.FloatField(null=True, blank=True)
    bank_account = models.CharField(max_length=100, blank=True)

    logo        = CloudinaryField("restaurant_logos",  null=True, blank=True)
    cover_image = CloudinaryField("restaurant_covers", null=True, blank=True)

    rating    = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    is_open   = models.BooleanField(default=True)

    delivery_fee      = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        verbose_name="رسوم التوصيل"
    )
    estimated_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name="وقت التوصيل التقديري (دقيقة)"
    )

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_visible_to_clients(self):
        return (
            self.approval_status == self.ApprovalStatus.APPROVED
            and self.is_open
        )

    @property
    def total_orders(self):
        return self.orders.count()

    class Meta:
        verbose_name        = "مطعم"
        verbose_name_plural = "المطاعم"

    def __str__(self):
        return self.name


# ══════════════════════════════════════════
#  أوقات العمل
# ══════════════════════════════════════════
class WorkingHours(models.Model):
    class Day(models.IntegerChoices):
        MONDAY    = 0, "الاثنين"
        TUESDAY   = 1, "الثلاثاء"
        WEDNESDAY = 2, "الأربعاء"
        THURSDAY  = 3, "الخميس"
        FRIDAY    = 4, "الجمعة"
        SATURDAY  = 5, "السبت"
        SUNDAY    = 6, "الأحد"

    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="working_hours"
    )
    day        = models.IntegerField(choices=Day.choices)
    open_time  = models.TimeField()
    close_time = models.TimeField()
    is_active  = models.BooleanField(default=True)

    class Meta:
        unique_together     = ("restaurant", "day")
        verbose_name        = "وقت عمل"
        verbose_name_plural = "أوقات العمل"

    def __str__(self):
        return f"{self.restaurant.name} - {self.get_day_display()}"


# ══════════════════════════════════════════
#  القائمة
# ══════════════════════════════════════════
class Menu(models.Model):
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, related_name="menus"
    )
    name       = models.CharField(max_length=150)
    time_label = models.CharField(max_length=150, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "قائمة"
        verbose_name_plural = "القوائم"

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"


# ══════════════════════════════════════════
#  المنتج
# ══════════════════════════════════════════
class Product(models.Model):
    class DisplayType(models.TextChoices):
        NORMAL   = "normal",   "عادي"
        DISCOUNT = "discount", "تخفيضات"

    menu        = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="products")
    name        = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    image       = CloudinaryField("product_images", null=True, blank=True)

    display_type     = models.CharField(
        max_length=20,
        choices=DisplayType.choices,
        default=DisplayType.NORMAL,
    )
    discount_percent = models.PositiveIntegerField(default=0)
    is_available     = models.BooleanField(default=True)

    rating     = models.DecimalField(
        max_digits=3, decimal_places=1, default=0,
        verbose_name="تقييم المنتج"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def final_price(self):
        if self.display_type == self.DisplayType.DISCOUNT and self.discount_percent:
            return self.price * (
                Decimal(1) - Decimal(self.discount_percent) / Decimal(100)
            )
        return self.price

    class Meta:
        verbose_name        = "منتج"
        verbose_name_plural = "المنتجات"

    def __str__(self):
        return f"{self.name} - {self.menu.restaurant.name}"


# ══════════════════════════════════════════
#  العروض والترقيات  (PromoScreen)
# ══════════════════════════════════════════
class Promotion(models.Model):
    title       = models.CharField(max_length=200, verbose_name="عنوان العرض")
    description = models.TextField(blank=True,     verbose_name="وصف العرض")
    image       = CloudinaryField("promotion_images", null=True, blank=True)

    restaurant  = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="promotions",
        verbose_name="المطعم",
    )

    discount_percent = models.PositiveIntegerField(
        default=0, verbose_name="نسبة الخصم %"
    )

    is_active  = models.BooleanField(default=True,  verbose_name="نشط")
    start_date = models.DateField(null=True, blank=True, verbose_name="تاريخ البداية")
    end_date   = models.DateField(null=True, blank=True, verbose_name="تاريخ الانتهاء")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ["-created_at"]
        verbose_name        = "عرض ترويجي"
        verbose_name_plural = "العروض الترويجية"

    def __str__(self):
        return self.title

# ✅ تم حذف Favorite من هنا — انتقل إلى favorites/models.py
