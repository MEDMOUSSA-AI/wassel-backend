from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT     = "client",     "عميل"
        LIVREUR    = "livreur",    "مندوب توصيل"
        RESTAURANT = "restaurant", "مطعم"
        ADMIN      = "admin",      "أدمن"

    role      = models.CharField(max_length=20, choices=Role.choices)
    phone     = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150, blank=True)

    # ✅ حقول مضافة لدعم PATCH /api/auth/me/
    address = models.CharField(max_length=255, blank=True, default='')
    lat     = models.FloatField(null=True, blank=True)
    lng     = models.FloatField(null=True, blank=True)
    avatar  = models.ImageField(upload_to='avatars/', null=True, blank=True)

    USERNAME_FIELD  = "username"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.phone
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name or self.username} ({self.get_role_display()})"


class ClientProfile(models.Model):
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_profile")
    default_address = models.CharField(max_length=255, blank=True)
    default_lat     = models.FloatField(null=True, blank=True)
    default_lng     = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"عميل: {self.user.full_name}"


class SavedAddress(models.Model):
    client     = models.ForeignKey(ClientProfile, on_delete=models.CASCADE, related_name="addresses")
    icon       = models.CharField(max_length=10, default="📍")
    name       = models.CharField(max_length=100)
    address    = models.CharField(max_length=255)
    lat        = models.FloatField()
    lng        = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.client.user.full_name}"


class LivreurProfile(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING  = "pending",  "قيد المراجعة"
        APPROVED = "approved", "موافق عليه"
        REJECTED = "rejected", "مرفوض"

    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name="livreur_profile")
    address          = models.CharField(max_length=255, blank=True)
    vehicle_plate    = models.CharField(max_length=30, blank=True)
    vehicle_model    = models.CharField(max_length=100, blank=True)
    bank_account     = models.CharField(max_length=100, blank=True)
    id_document      = models.ImageField(upload_to="livreur_documents/", null=True, blank=True)
    license_document = models.ImageField(upload_to="livreur_documents/", null=True, blank=True)

    approval_status = models.CharField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING
    )
    is_online   = models.BooleanField(default=False)
    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)

    balance         = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_rate = models.DecimalField(max_digits=4, decimal_places=2, default=0.10)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"مندوب: {self.user.full_name} ({self.approval_status})"
