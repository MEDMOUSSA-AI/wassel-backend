from django.contrib import admin

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("subtotal",)


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("status", "timestamp")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "order_type", "client", "restaurant", "livreur",
        "status", "total_price", "created_at",
    )
    list_filter = ("order_type", "status", "payment_method")
    search_fields = ("client__phone", "client__full_name", "restaurant__name")
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    readonly_fields = ("created_at", "updated_at")
