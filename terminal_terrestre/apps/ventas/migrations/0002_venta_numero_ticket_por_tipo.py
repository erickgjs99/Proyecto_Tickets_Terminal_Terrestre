# Migration: numero_ticket deja de ser unique global y pasa a unique_together con tipo_ticket

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ventas', '0001_initial'),
    ]

    operations = [
        # 1. Quitar el unique global de numero_ticket
        migrations.AlterField(
            model_name='venta',
            name='numero_ticket',
            field=models.CharField(
                db_index=True,
                help_text='Formato: TK-000001. Secuencial por tipo de ticket.',
                max_length=20,
                verbose_name='Número de ticket',
            ),
        ),
        # 2. Añadir unique_together (tipo_ticket, numero_ticket)
        migrations.AlterUniqueTogether(
            name='venta',
            unique_together={('tipo_ticket', 'numero_ticket')},
        ),
    ]
