import os

from django.conf import settings
from django.core.files import File
from django.db import migrations

from siteapp.imaging import resize_and_compress


def copy_static_images_into_upload_field(apps, schema_editor):
    HeroImage = apps.get_model('siteapp', 'HeroImage')

    for hero in HeroImage.objects.exclude(image_url='').filter(image=''):
        src_path = os.path.join(settings.BASE_DIR, 'static', hero.image_url)
        if not os.path.exists(src_path):
            continue

        with open(src_path, 'rb') as f:
            hero.image.save(os.path.basename(src_path), File(f), save=True)

        resize_and_compress(hero.image)
        HeroImage.objects.filter(pk=hero.pk).update(image=hero.image.name)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('siteapp', '0010_document_file_heroimage_image_and_more'),
    ]

    operations = [
        migrations.RunPython(copy_static_images_into_upload_field, noop),
    ]
