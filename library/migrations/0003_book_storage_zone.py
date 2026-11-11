from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0002_book_shelf_location"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="storage_zone",
            field=models.CharField("Зона хранения", blank=True, max_length=24, null=True),
        ),
    ]
