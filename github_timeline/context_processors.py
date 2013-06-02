from django.conf import settings

def common(request):
    """
    Adds site config context variables to the context.

    """
    return {'IMAGES_URL': settings.IMAGES_URL,
            'STATIC_URL': settings.STATIC_URL
            }