from django.contrib import admin

from .models import LiveTrackingPoint


@admin.register(LiveTrackingPoint)
class LiveTrackingPointAdmin(admin.ModelAdmin):
    list_display = ("order", "lat", "lng", "timestamp")
    list_filter = ("timestamp",)
    search_fields = ("order__id",)
