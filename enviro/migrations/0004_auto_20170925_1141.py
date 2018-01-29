# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-09-25 11:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enviro', '0003_auto_20170923_1844'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributionmodel',
            name='distribution',
            field=models.CharField(choices=[('Normal', 'Normal Distribution'), ('Weibull', 'Weibull'), ('Lognormal_2', 'Log-Normal'), ('KernelDensity', 'Kernel Density')], max_length=15),
        ),
    ]