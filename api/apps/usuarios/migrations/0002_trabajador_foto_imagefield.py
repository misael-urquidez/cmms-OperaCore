from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trabajador',
            name='foto',
            field=models.ImageField(blank=True, max_length=255, null=True, upload_to='trabajadores/'),
        ),
    ]
