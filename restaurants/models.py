from decimal import Decimal

from django.db import models
from accounts.models import User


class RestaurantCategory(models.Model):
    """
    تصنيف المطاعم: مخبزة، مطعم، عصائر... كما يظهر في شاشة العميل الرئيسية.
    """
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to="category_images/", null=True, blank=True)

    class Meta:
        verbose_name_plural = "Restaurant Categories"

    def __str__(self):
        return self.name


class Restaurant(models.Model):
    """
    المطعم. يسجّل صاحب المطعم بنفسه، وتبقى approval_status = pending
    حتى يوافق الأدمن — بعدها فقط يظهر للعملاء (is_visible_to_clients).
    """

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "قيد المراجعة"
        APPROVED = "approved", "موافق عليه"
        REJECTED = "rejected", "مرفوض"

    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="restaurant")
    name = models.CharField(max_length=150)
    owner_name = models.CharField(max_length=150)
    category = models.ForeignKey(
        RestaurantCategory, on_delete=models.SET_NULL, null=True, related_name="restaurants"
    )

    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    bank_account = models.CharField(max_length=100, blank=True)

    logo = models.ImageField(upload_to="restaurant_logos/", null=True, blank=True)
    cover_image = models.ImageField(upload_to="restaurant_covers/", null=True, blank=True)

    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    is_open = models.BooleanField(default=True)  # مفتوح الآن يدوياً من المطعم
    approval_status = models.CharField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_visible_to_clients(self):
        return self.approval_status == self.ApprovalStatus.APPROVED and self.is_open

    def __str__(self):
        return self.name


class WorkingHours(models.Model):
    """
    أيام وساعات عمل المطعم — مطابق لـ _DaysSelector في شاشة تسجيل المطعم.
    """

    class Day(models.IntegerChoices):
        MONDAY = 0, "الاثنين"
        TUESDAY = 1, "الثلاثاء"
        WEDNESDAY = 2, "الأربعاء"
        THURSDAY = 3, "الخميس"
        FRIDAY = 4, "الجمعة"
        SATURDAY = 5, "السبت"
        SUNDAY = 6, "الأحد"

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="working_hours")
    day = models.IntegerField(choices=Day.choices)
    open_time = models.TimeField()
    close_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("restaurant", "day")

    def __str__(self):
        return f"{self.restaurant.name} - {self.get_day_display()}"


class Menu(models.Model):
    """
    قائمة ضمن المطعم (القائمة الرئيسية، قائمة الإفطار...).
    مطعم واحد قد يملك عدة قوائم حسب الوقت.
    """
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="menus")
    name = models.CharField(max_length=150)
    time_label = models.CharField(max_length=150, blank=True)  # مثال: الاثنين-الأحد 08:00-22:00
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.restaurant.name})"


class Product(models.Model):
    """
    صنف طعام ضمن قائمة معينة — مطابق لحقول RestaurantProductFormScreen في Flutter.
    """

    class DisplayType(models.TextChoices):
        NORMAL = "normal", "عادي"
        DISCOUNT = "discount", "تخفيضات"

    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="product_images/", null=True, blank=True)

    display_type = models.CharField(
        max_length=20, choices=DisplayType.choices, default=DisplayType.NORMAL
    )
    discount_percent = models.PositiveIntegerField(default=0)  # فقط إذا display_type = discount

    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def final_price(self):
        if self.display_type == self.DisplayType.DISCOUNT and self.discount_percent:
            return self.price * (Decimal(1) - Decimal(self.discount_percent) / Decimal(100))
        return self.price

    def __str__(self):
        return f"{self.name} - {self.menu.restaurant.name}"
