from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),

    # REST API
    path('api/auth/',          include('accounts.urls')),
    path('api/restaurants/',   include('restaurants.urls')),
    path('api/orders/',        include('orders.urls')),
    path('api/delivery/',      include('delivery.urls')),
    path('api/promotions/',    include('restaurants.promo_urls')),   # ✅ العروض
    path('api/favorites/',     include('favorites.urls')),           # ✅ المفضلة
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
