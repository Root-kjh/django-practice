from django.db import models, transaction
from copy import deepcopy

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
    translate_from_study = models.ForeignKey('self', null=True, blank=True, related_name='translated_studies', verbose_name="번역 원본 임상연구(study) 고유번호", on_delete=models.CASCADE)
    clone_from_study = models.OneToOneField('self', null=True, blank=True, related_name='cloned_study', verbose_name="복제 원본 임상연구(study) 고유번호", on_delete=models.CASCADE)
    locale = models.CharField(max_length=2, verbose_name="언어코드", null=True, blank=True)

    @transaction.atomic
    def clone(self):
        cloned_study = self._clone_study()
        for translated_study in self.translated_studies.all():
            translated_study._clone_study()
        return cloned_study

    def _clone_study(self):
        cloned_study = deepcopy(self)
        cloned_study.pk = None
        cloned_study.clone_from_study = self
        if self.translate_from_study is None:
            cloned_study.translate_from_study = None
        else:
            cloned_study.translate_from_study = self.translate_from_study.cloned_study
        cloned_study.save()

        for intervention in self.interventions.all():
            intervention.clone(cloned_study)

        for condition in self.conditions.all():
            cloned_study.conditions.add(condition)
        
        for eligibility in self.eligibilities.all():
            eligibility.clone(cloned_study)
        return cloned_study

    def save(self, *args, **kwargs) -> None:
        if self.control_status_type == ControlStatusType.COMPLETED and self.clone_from_study is not None:
            clone_from_study_id = self.clone_from_study_id
            self.translated_studies.all().update(clone_from_study=None)
            self.clone_from_study = None
            self.save()
            Study.objects.filter(id=clone_from_study_id).delete()
            return
        return super().save(*args, **kwargs)

    class Meta:
        unique_together = ('translate_from_study', 'locale')

        
class Intervention(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="interventions")
    intervention_type = models.CharField(max_length=500, verbose_name="치료 타입", null=True, blank=True)
    name = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    translate_from_intervention = models.ForeignKey('self', null=True, blank=True, related_name='translated_interventions', verbose_name="번역 원본 의약품(intervention) 고유번호", on_delete=models.CASCADE)
    clone_from_intervention = models.OneToOneField('self', null=True, blank=True, related_name='cloned_intervention', verbose_name="복제 원본 의약품(intervention) 고유번호", on_delete=models.CASCADE)
    locale = models.CharField(max_length=2, verbose_name="언어코드", null=True, blank=True)

    def clone(self, study):
        cloned_intervention = deepcopy(self)
        cloned_intervention.clone_from_intervention = self
        cloned_intervention.pk = None
        cloned_intervention.study = study
        if self.translate_from_intervention is not None:
            cloned_intervention.translate_from_intervention = self.translate_from_intervention.cloned_intervention
        cloned_intervention.save()
        return cloned_intervention
    
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
    translate_from_eligibility = models.ForeignKey('self', null=True, blank=True, related_name='translated_eligibilities', verbose_name="번역 원본 선정조건(eligibility) 고유번호", on_delete=models.CASCADE)
    clone_from_eligibility = models.OneToOneField('self', null=True, blank=True, related_name='cloned_eligibility', verbose_name="복제 원본 선정조건(eligibility) 고유번호", on_delete=models.CASCADE)
    locale = models.CharField(max_length=2, verbose_name="언어코드", null=True, blank=True)

    def clone(self, study):
        cloned_eligibility = deepcopy(self)
        cloned_eligibility.pk = None
        cloned_eligibility.study = study
        cloned_eligibility.clone_from_eligibility = self
        if self.translate_from_eligibility is not None:
            cloned_eligibility.translate_from_eligibility = self.translate_from_eligibility.clone_from_eligibility
        cloned_eligibility.save()
        return cloned_eligibility
        
                
            


class ConfigurationVariable(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="변수명")
    value = models.CharField(max_length=100, verbose_name="값")