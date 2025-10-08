from .models import HeroImage

def hero_images(request):
    qs = HeroImage.objects.filter(is_active=True).order_by('order')
    return {"hero": qs}
