from django.contrib import admin

from .models import RestaurantCategory, Restaurant, WorkingHours, Menu, Product


@admin.register(RestaurantCategory)
class RestaurantCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class WorkingHoursInline(admin.TabularInline):
    model = WorkingHours
    extra = 1


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "owner_name", "city", "category", "approval_status", "is_open", "rating")
    list_filter = ("approval_status", "is_open", "city", "category")
    search_fields = ("name", "owner_name", "owner__phone")
    inlines = [WorkingHoursInline]
    actions = ["approve_restaurants", "reject_restaurants"]

    @admin.action(description="الموافقة على المطاعم المختارة")
    def approve_restaurants(self, request, queryset):
        queryset.update(approval_status=Restaurant.ApprovalStatus.APPROVED)

    @admin.action(description="رفض المطاعم المختارة")
    def reject_restaurants(self, request, queryset):
        queryset.update(approval_status=Restaurant.ApprovalStatus.REJECTED)


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "restaurant__name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "menu", "price", "display_type", "discount_percent", "is_available")
    list_filter = ("display_type", "is_available")
    search_fields = ("name", "menu__restaurant__name")
