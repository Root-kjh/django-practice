from django.db import models

from .assets import ControlStatusType

class Study(models.Model):
    nct_id = models.CharField(verbose_name="임상연구 번호", max_length=50)
    control_status_type = models.CharField(max_length=50, verbose_name="임상연구 적재 상태", null=True, blank=True, choices=ControlStatusType.choices)
    original_data = models.TextField(verbose_name="원본 데이터", null=True, blank=True)
    original_data_hash = models.CharField(max_length=64, verbose_name="original_data sha256 hash", null=True, blank=True)
    results_first_submitted_date = models.DateField(verbose_name="최초 제출 날짜", null=True, blank=True)
    last_update_submitted_date = models.DateField(verbose_name="최근 수정 날짜", null=True, blank=True)
    start_date = models.DateField(verbose_name="임상연구 시작 날짜", null=True, blank=True)
    completion_date = models.DateField(verbose_name="임상연구 종료 날짜", null=True, blank=True)
    title = models.TextField(verbose_name="제목", null=True, blank=True)
    overall_status = models.CharField(max_length=50, verbose_name="진행 상태", null=True, blank=True)
    phase = models.CharField(max_length=50, verbose_name="임상 단계", null=True, blank=True)
    enrollment = models.IntegerField(verbose_name="대상자 수", null=True, blank=True)
    original_study = models.ForeignKey('self', null=True, blank=True, related_name='translated_studies', verbose_name="원본 임상연구(study) 고유번호", on_delete=models.CASCADE)
    locale = models.CharField(max_length=2, verbose_name="언어코드", null=True, blank=True)

    class Meta:
        unique_together = ('original_study', 'locale',)

        
class Intervention(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="interventions")
    intervention_type = models.CharField(max_length=500, verbose_name="치료 타입", null=True, blank=True)
    name = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    original_intervention = models.ForeignKey('self', null=True, blank=True, related_name='translated_interventions', verbose_name="원본 의약품(intervention) 고유번호", on_delete=models.CASCADE)
    locale = models.CharField(max_length=2, verbose_name="언어코드", null=True, blank=True)
    
class Condition(models.Model):
    studies = models.ManyToManyField(Study, related_name="conditions")
    name = models.CharField(max_length=500, null=True, blank=True)
    original_condition = models.ForeignKey('self', null=True, blank=True, related_name='translated_conditions', verbose_name="원본 질환(condition) 고유번호", on_delete=models.CASCADE)
    locale = models.CharField(max_length=2, verbose_name="언어코드", null=True, blank=True)
    
class Eligibility(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="eligibilities")
    gender = models.TextField(verbose_name="성별", null=True, blank=True)
    minimum_age = models.CharField(max_length=30, verbose_name="최소 나이", null=True, blank=True)
    maximum_age = models.CharField(max_length=30, verbose_name="최대 나이", null=True, blank=True)
    healthy_volunteers = models.TextField(null=True, blank=True)
    criteria = models.TextField(null=True, blank=True)
    original_eligibility = models.ForeignKey('self', null=True, blank=True, related_name='translated_eligibility', verbose_name="원본 선정조건(eligibility) 고유번호", on_delete=models.CASCADE)
    locale = models.CharField(max_length=2, verbose_name="언어코드", null=True, blank=True)

class ConfigurationVariable(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="변수명")
    value = models.CharField(max_length=100, verbose_name="값")