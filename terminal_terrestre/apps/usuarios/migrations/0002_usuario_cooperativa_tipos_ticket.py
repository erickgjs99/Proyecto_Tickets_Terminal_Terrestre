# Migration: agrega cooperativa y tipos_ticket_permitidos a Usuario

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
        ('cooperativas', '0001_initial'),
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='cooperativa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='usuarios',
                to='cooperativas.cooperativa',
                verbose_name='Cooperativa asignada',
            ),
        ),
        migrations.AddField(
            model_name='usuario',
            name='tipos_ticket_permitidos',
            field=models.ManyToManyField(
                blank=True,
                help_text='Tipos de ticket que este usuario puede generar. Vacío = todos (solo admin/supervisor).',
                related_name='operadores_permitidos',
                to='tickets.tipoticket',
                verbose_name='Tipos de ticket permitidos',
            ),
        ),
    ]
