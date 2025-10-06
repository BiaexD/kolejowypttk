from django.conf import settings

def site_context(request):
    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", ""),
        "SITE_TAGLINE": getattr(settings, "SITE_TAGLINE", ""),
        "FACEBOOK_PAGE_URL": getattr(settings, "FACEBOOK_PAGE_URL", ""),
        "ORG_ADDRESS": getattr(settings, "ORG_ADDRESS", ""),
        "ORG_EMAIL": getattr(settings, "ORG_EMAIL", ""),
        "ORG_PHONE": getattr(settings, "ORG_PHONE", ""),
        "ORG_NIP": getattr(settings, "ORG_NIP", ""),
        "ORG_REGON": getattr(settings, "ORG_REGON", ""),
        "ORG_KRS": getattr(settings, "ORG_KRS", ""),
    }
