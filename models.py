from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    مستخدم موحد لكل الأدوار: عميل، مندوب، مطعم، أدمن.
    نستخدم نفس جدول auth الافتراضي لكن نضيف حقل role ورقم هاتف فريد،
    لأن تسجيل الدخول الفعلي في التطبيق يعتمد على رقم الهاتف.
    """

    class Role(models.TextChoices):
        CLIENT = "client", "عميل"
        LIVREUR = "livreur", "مندوب توصيل"
        RESTAURANT = "restaurant", "مطعم"
        ADMIN = "admin", "أدمن"

    role = models.CharField(max_length=20, choices=Role.choices)
    phone = models.CharField(max_length=20, unique=True)

    # الحقول التالية اختيارية حسب الدور (مثلاً المطعم له اسم منفصل في app آخر)
    full_name = models.CharField(max_length=150, blank=True)

    # نستخدم الهاتف كمعرف دخول رئيسي بدل username التقليدي،
    # لكن نُبقي username لأن AbstractUser يتطلبه داخلياً (سنملأه تلقائياً = phone).
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        # نجعل username = phone تلقائياً لتفادي تكرار الإدخال يدوياً
        if not self.username:
            self.username = self.phone
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name or self.username} ({self.get_role_display()})"


class ClientProfile(models.Model):
    """
    بيانات إضافية خاصة بالعميل فقط.
    العميل يسجل دخوله باسم + هاتف فقط (بدون كلمة مرور) حسب تصميم التطبيق الحالي.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_profile")
    default_address = models.CharField(max_length=255, blank=True)
    default_lat = models.FloatField(null=True, blank=True)
    default_lng = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"عميل: {self.user.full_name}"


class SavedAddress(models.Model):
    """
    عناوين محفوظة للعميل (المنزل، العمل...) — مطابق لـ SavedAddress في Flutter.
    """
    client = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name="addresses")
    icon = models.CharField(max_length=10, default="📍")
    name = models.CharField(max_length=100)  # مثال: المنزل، العمل
    address = models.CharField(max_length=255)
    lat = models.FloatField()
    lng = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.client.user.full_name}"


class LivreurProfile(models.Model):
    """
    بيانات المندوب: مركبة، حساب بنكي، وثائق، حالة الموافقة، الرصيد.
    """

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "قيد المراجعة"
        APPROVED = "approved", "موافق عليه"
        REJECTED = "rejected", "مرفوض"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="livreur_profile")
    address = models.CharField(max_length=255, blank=True)
    vehicle_plate = models.CharField(max_length=30, blank=True)
    vehicle_model = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=100, blank=True)
    id_document = models.ImageField(upload_to="livreur_documents/", null=True, blank=True)
    license_document = models.ImageField(upload_to="livreur_documents/", null=True, blank=True)

    approval_status = models.CharField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING
    )
    is_online = models.BooleanField(default=False)  # متاح لاستقبال طلبات الآن أم لا
    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)

    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_rate = models.DecimalField(max_digits=4, decimal_places=2, default=0.10)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"مندوب: {self.user.full_name} ({self.approval_status})"
