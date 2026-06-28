from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Favorite
from restaurants.models import Product


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def favorites_list(request):
    if request.method == "GET":
        favs = Favorite.objects.filter(user=request.user).select_related(
            "product__menu__restaurant"
        )
        return Response([_fav_dict(f) for f in favs])

    # POST — إضافة للمفضلة
    menu_item_id = request.data.get("menu_item_id")
    if not menu_item_id:
        return Response({"detail": "menu_item_id مطلوب."}, status=400)

    product = get_object_or_404(Product, pk=menu_item_id)
    fav, created = Favorite.objects.get_or_create(
        user=request.user, product=product
    )
    return Response(_fav_dict(fav), status=201 if created else 200)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def favorites_detail(request, pk):
    fav = get_object_or_404(Favorite, pk=pk, user=request.user)
    fav.delete()
    return Response({"detail": "تم الحذف."}, status=204)


def _fav_dict(fav):
    p = fav.product
    return {
        "id":              fav.id,
        "menu_item_id":    p.id,
        "name":            p.name,
        "description":     p.description or "",
        "image":           p.image.url if p.image else "",
        "price":           float(p.final_price),
        "restaurant_name": p.menu.restaurant.name if p.menu else "",
    }
