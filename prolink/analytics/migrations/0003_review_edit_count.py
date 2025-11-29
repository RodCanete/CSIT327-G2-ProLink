# Generated manually to add edit_count field to Review model

from django.db import migrations, models


def set_default_edit_count(apps, schema_editor):
    """Set default edit_count to 0 for existing reviews"""
    Review = apps.get_model('analytics', 'Review')
    Review.objects.filter(edit_count__isnull=True).update(edit_count=0)


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_delete_transaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='edit_count',
            field=models.IntegerField(default=0, help_text='Number of times this review has been edited'),
        ),
        migrations.RunPython(set_default_edit_count, migrations.RunPython.noop),
    ]

