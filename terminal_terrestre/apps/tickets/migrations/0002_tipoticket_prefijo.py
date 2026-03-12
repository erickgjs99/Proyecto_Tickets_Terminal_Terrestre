# Migration: agrega campo prefijo a TipoTicket

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipoticket',
            name='prefijo',
            field=models.CharField(
                default='TK',
                help_text='Siglas del número de ticket. Ej: BIP → BIP-000001',
                max_length=10,
                verbose_name='Prefijo de numeración',
            ),
        ),
    ]
