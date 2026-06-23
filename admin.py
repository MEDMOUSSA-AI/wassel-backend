from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, ClientProfile, SavedAddress, LivreurProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "phone", "full_name", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("phone", "full_name", "username")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("بيانات وصل", {"fields": ("role", "phone", "full_name")}),
    )


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "default_address")
    search_fields = ("user__full_name", "user__phone")


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "address")
    search_fields = ("client__user__full_name", "name")


@admin.register(LivreurProfile)
class LivreurProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "vehicle_plate", "approval_status", "is_online", "balance")
    list_filter = ("approval_status", "is_online")
    search_fields = ("user__full_name", "user__phone", "vehicle_plate")
    actions = ["approve_livreurs", "reject_livreurs"]

    @admin.action(description="الموافقة على المناديب المختارين")
    def approve_livreurs(self, request, queryset):
        queryset.update(approval_status=LivreurProfile.ApprovalStatus.APPROVED)

    @admin.action(description="رفض المناديب المختارين")
    def reject_livreurs(self, request, queryset):
        queryset.update(approval_status=LivreurProfile.ApprovalStatus.REJECTED)
