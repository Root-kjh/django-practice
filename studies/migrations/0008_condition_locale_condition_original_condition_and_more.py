# Generated by Django 4.1.6 on 2023-02-23 13:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('studies', '0007_configurationvariable'),
    ]

    operations = [
        migrations.AddField(
            model_name='condition',
            name='locale',
            field=models.CharField(blank=True, max_length=2, null=True, verbose_name='언어코드'),
        ),
        migrations.AddField(
            model_name='condition',
            name='original_condition',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translated_conditions', to='studies.condition', verbose_name='원본 질환(condition) 고유번호'),
        ),
        migrations.AddField(
            model_name='eligibility',
            name='locale',
            field=models.CharField(blank=True, max_length=2, null=True, verbose_name='언어코드'),
        ),
        migrations.AddField(
            model_name='eligibility',
            name='original_eligibility',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translated_eligibility', to='studies.eligibility', verbose_name='원본 선정조건(eligibility) 고유번호'),
        ),
        migrations.AddField(
            model_name='intervention',
            name='locale',
            field=models.CharField(blank=True, max_length=2, null=True, verbose_name='언어코드'),
        ),
        migrations.AddField(
            model_name='intervention',
            name='original_intervention',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translated_interventions', to='studies.intervention', verbose_name='원본 의약품(intervention) 고유번호'),
        ),
        migrations.AddField(
            model_name='study',
            name='locale',
            field=models.CharField(blank=True, max_length=2, null=True, verbose_name='언어코드'),
        ),
        migrations.AddField(
            model_name='study',
            name='original_study',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translated_studies', to='studies.study', verbose_name='원본 임상연구(study) 고유번호'),
        ),
        migrations.AlterField(
            model_name='eligibility',
            name='gender',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='성별'),
        ),
        migrations.AlterField(
            model_name='study',
            name='nct_id',
            field=models.CharField(max_length=50, verbose_name='임상연구 번호'),
        ),
        migrations.AlterUniqueTogether(
            name='study',
            unique_together={('original_study', 'locale')},
        ),
    ]
