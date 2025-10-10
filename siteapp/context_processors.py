from django.core.cache import cache
from .models import HeroImage

def hero_images(request):
    hero = cache.get("hero_images")
    if hero is None:
        hero = list(HeroImage.objects.filter(is_active=True).order_by("order")[:5])
        cache.set("hero_images", hero, 300)  # 5 min
    return {"hero": hero}