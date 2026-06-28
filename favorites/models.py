from django.db import models
from accounts.models import User
from restaurants.models import Product


class Favorite(models.Model):
    user    = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="العميل",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="المنتج",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together     = ("user", "product")
        ordering            = ["-created_at"]
        verbose_name        = "مفضلة"
        verbose_name_plural = "المفضلات"

    def __str__(self):
        return f"{self.user} ← {self.product}"
