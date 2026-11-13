from django.db import migrations

DEFAULT_TAGS = ["Marketing", "Social", "Personal", "Work"]


def seed_tags(apps, schema_editor):
    Tag = apps.get_model("shortener", "Tag")
    for name in DEFAULT_TAGS:
        Tag.objects.get_or_create(name=name)


def remove_tags(apps, schema_editor):
    Tag = apps.get_model("shortener", "Tag")
    Tag.objects.filter(name__in=DEFAULT_TAGS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shortener', '0003_click'),
    ]

    operations = [
        migrations.RunPython(seed_tags, remove_tags),
    ]
