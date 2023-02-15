from django.db import models

class Study(models.Model):
    nct_id = models.CharField(verbose_name="임상연구 번호", max_length=50, unique=True)
    results_first_submitted_date = models.DateField(verbose_name="최초 제출 날짜", null=True, blank=True)
    last_update_submitted_date = models.DateField(verbose_name="최근 수정 날짜", null=True, blank=True)
    start_date = models.DateField(verbose_name="임상연구 시작 날짜", null=True, blank=True)
    completion_date = models.DateField(verbose_name="임상연구 종료 날짜", null=True, blank=True)
    title = models.TextField(verbose_name="제목", null=True, blank=True)
    overall_status = models.CharField(max_length=50, verbose_name="진행 상태", null=True, blank=True)
    phase = models.CharField(max_length=50, verbose_name="임상 단계", null=True, blank=True)
    enrollment = models.IntegerField(verbose_name="대상자 수", null=True, blank=True)

class Intervention(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="interventions")
    intervention_type = models.CharField(max_length=50, verbose_name="치료 타입", null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
class Condition(models.Model):
    studies = models.ManyToManyField(Study, related_name="conditions")
    name = models.CharField(max_length=100, null=True, blank=True)
    
class Eligibility(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="eligibilities")
    gender = models.CharField(max_length=10, verbose_name="성별", null=True, blank=True)
    minimum_age = models.CharField(max_length=30, verbose_name="최소 나이", null=True, blank=True)
    maximum_age = models.CharField(max_length=30, verbose_name="최대 나이", null=True, blank=True)
    healthy_volunteers = models.CharField(max_length=100, null=True, blank=True)
    criteria = models.TextField(null=True, blank=True)

class ConfigurationVariable(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="변수명")
    value = models.CharField(max_length=100, verbose_name="값")