from django.contrib.auth.management import create_permissions
from django.db import migrations

FULL_CRUD_MODELS = [
    'post', 'postimage', 'event', 'eventphoto', 'person', 'document', 'heroimage',
]
VIEW_DELETE_ONLY_MODELS = ['centralnews']


def create_redaktor_group(apps, schema_editor):
    from django.apps import apps as global_apps

    # Permissions are normally created by a post_migrate signal that fires only
    # after the whole `migrate` run finishes, so on a fresh database they may
    # not exist yet at this point — create them explicitly first.
    create_permissions(global_apps.get_app_config('siteapp'), verbosity=0)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    group, _ = Group.objects.get_or_create(name='Redaktorzy')

    codenames = [f'{action}_{model}' for model in FULL_CRUD_MODELS for action in ('add', 'change', 'delete', 'view')]
    codenames += [f'{action}_{model}' for model in VIEW_DELETE_ONLY_MODELS for action in ('delete', 'view')]

    perms = Permission.objects.filter(content_type__app_label='siteapp', codename__in=codenames)
    group.permissions.set(perms)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('siteapp', '0011_migrate_hero_images'),
    ]

    operations = [
        migrations.RunPython(create_redaktor_group, noop),
    ]
