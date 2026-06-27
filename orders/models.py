from django.db import models
from accounts.models import User
from restaurants.models import Restaurant, Product


class Order(models.Model):
    """
    طلب موحّد يدعم نوعين (مطابق لـ OrderType في livreur_order_types.dart):
    - FOOD: طلبية من مطعم (له restaurant و OrderItems)
    - PARCEL: توصيلة طرد مباشرة (بدون مطعم، فقط من → إلى)
    """

    class OrderType(models.TextChoices):
        FOOD = "food", "طلبية مطعم"
        PARCEL = "parcel", "توصيلة طرد"

    class Status(models.TextChoices):
        PENDING = "pending", "بانتظار تأكيد المطعم"
        CONFIRMED = "confirmed", "تم تأكيد البائع"
        SEARCHING_LIVREUR = "searching_livreur", "جاري البحث عن مندوب"
        ACCEPTED = "accepted", "تم قبول المندوب"
        PICKED_UP = "picked_up", "تم الاستلام من المطعم"
        ON_THE_WAY = "on_the_way", "في الطريق"
        DELIVERED = "delivered", "تم التوصيل"
        CANCELLED = "cancelled", "ملغى"

    order_type = models.CharField(max_length=10, choices=OrderType.choices)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    livreur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="deliveries"
    )

    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)

    pickup_address = models.CharField(max_length=255)
    pickup_lat = models.FloatField()
    pickup_lng = models.FloatField()

    dropoff_address = models.CharField(max_length=255)
    dropoff_lat = models.FloatField()
    dropoff_lng = models.FloatField()

    recipient_name = models.CharField(max_length=150, blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    parcel_notes = models.TextField(blank=True)

    items_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    distance_km = models.FloatField(null=True, blank=True)
    estimated_minutes = models.PositiveIntegerField(null=True, blank=True)

    payment_method = models.CharField(max_length=20, default="cash")

    # ✅ حقل التقييم — مضاف
    rating = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def livreur_commission(self):
        if self.livreur and hasattr(self.livreur, "livreur_profile"):
            rate = self.livreur.livreur_profile.commission_rate
        else:
            rate = 0.10
        return self.delivery_fee * rate

    @property
    def livreur_net_fee(self):
        return self.delivery_fee - self.livreur_commission

    @property
    def restaurant_amount(self):
        if self.order_type == self.OrderType.FOOD:
            return self.items_price * 0.90
        return 0

    def __str__(self):
        return f"طلب #{self.id} - {self.get_order_type_display()} - {self.client}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="order_items")

    product_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=30, choices=Order.Status.choices)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_id} -> {self.status} @ {self.timestamp}"
