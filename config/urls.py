from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import JsonResponse
import os, cloudinary, cloudinary.uploader

def cloudinary_test(request):
    # اختبار رفع صورة بسيطة لـ Cloudinary
    try:
        result = cloudinary.uploader.upload(
            "https://via.placeholder.com/100.png",
            folder="wassel/test",
            public_id="test_connection"
        )
        return JsonResponse({
            'status': 'success',
            'url': result.get('secure_url'),
            'cloud_name': os.getenv('CLOUDINARY_CLOUD_NAME'),
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'cloud_name': os.getenv('CLOUDINARY_CLOUD_NAME'),
            'api_key': os.getenv('CLOUDINARY_API_KEY'),
            'has_secret': bool(os.getenv('CLOUDINARY_API_SECRET')),
        })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),

    # ── اختبار مؤقت ──
    path('test-cloudinary/', cloudinary_test),

    # REST API
    path('api/auth/',          include('accounts.urls')),
    path('api/restaurants/',   include('restaurants.urls')),
    path('api/orders/',        include('orders.urls')),
    path('api/delivery/',      include('delivery.urls')),
    path('api/promotions/',    include('restaurants.promo_urls')),
    path('api/favorites/',     include('favorites.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
