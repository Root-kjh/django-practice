from django.db import models

class Study(models.Model):
    nct_id = models.CharField(verbose_name="임상연구 번호", max_length=50)
    results_first_submitted_date = models.DateField(verbose_name="최초 제출 날짜")
    last_update_submitted_date = models.DateField(verbose_name="최근 수정 날짜")
    start_date = models.DateField(verbose_name="임상연구 시작 날짜")
    completion_date = models.DateField(verbose_name="임상연구 종료 날짜")
    title = models.CharField(max_length=300, verbose_name="제목")
    overall_status = models.CharField(max_length=50, verbose_name="진행 상태")
    phase = models.CharField(max_length=50, verbose_name="임상 단계")
    enrollment = models.IntegerField(verbose_name="대상자 수")

class Intervention(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    intervention_type = models.CharField(max_length=50, verbose_name="치료 타입")
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    
class Condition(models.Model):
    studies = models.ManyToManyField(Study, related_name="conditions")
    name = models.CharField(max_length=100)
    
class Eligibility(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    sampling_method = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, verbose_name="성별")
    minimum_age = models.CharField(max_length=30, verbose_name="최소 나이")
    maximum_age = models.CharField(max_length=30, verbose_name="최대 나이")
    healthy_volunteers = models.CharField(max_length=100)
    population = models.TextField()
    criteria = models.TextField()
    gender_description = models.TextField()
    gender_based = models.TextField()