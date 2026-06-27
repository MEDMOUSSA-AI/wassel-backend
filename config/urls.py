from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import JsonResponse
import os, cloudinary, cloudinary.uploader

def cloudinary_test(request):
    # صورة 1x1 pixel بـ base64
    import base64
    tiny_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    try:
        import tempfile, os as _os
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(tiny_png)
            tmp_path = f.name
        result = cloudinary.uploader.upload(
            tmp_path,
            folder="wassel/test",
            public_id="test_connection"
        )
        _os.unlink(tmp_path)
        return JsonResponse({
            'status': 'success ✅',
            'url': result.get('secure_url'),
            'cloud_name': os.getenv('CLOUDINARY_CLOUD_NAME'),
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error ❌',
            'error': str(e),
        })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('test-cloudinary/', cloudinary_test),
    path('api/auth/',          include('accounts.urls')),
    path('api/restaurants/',   include('restaurants.urls')),
    path('api/orders/',        include('orders.urls')),
    path('api/delivery/',      include('delivery.urls')),
    path('api/promotions/',    include('restaurants.promo_urls')),
    path('api/favorites/',     include('favorites.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
