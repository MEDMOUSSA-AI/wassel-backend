from django.db import models
from orders.models import Order


class LiveTrackingPoint(models.Model):
    """
    نقطة موقع لحظية للمندوب أثناء تنفيذ طلب معين.
    تُستخدم لرسم مسار الحركة في شاشة تتبع الطلب عند العميل (client_orders_track_screen).
    نحتفظ بسجل تاريخي بسيط بدل تحديث صف واحد فقط، لإتاحة عرض المسار لاحقاً إن لزم.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tracking_points")
    lat = models.FloatField()
    lng = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"موقع طلب #{self.order_id} @ {self.timestamp}"
