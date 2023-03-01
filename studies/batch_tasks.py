import requests
from rest_framework.exceptions import ValidationError
from tqdm import tqdm
from time import sleep
from translate import Translator
from django.db import transaction
from django.db.models import Prefetch
import traceback
import hashlib
import json
from copy import deepcopy

from .models import ConfigurationVariable, Study, Condition, Intervention, Eligibility
from .assets import ControlStatusType
from .serializers import StudySerializer

TRANSLATE_FIELDS = ['title', 'overall_status', 'phase']

def get_original_data_hash(original_data):
    return hashlib.sha256(json.dumps(original_data).encode('utf-8')).hexdigest()

def get_nct_id(study):
    return study['Study']['ProtocolSection']['IdentificationModule']['NCTId']

def get_studies_num():
    """
    clinicaltrials.gov 에 존재하는 임상 연구 개수를 가져오는 메소드
    """
    CLINICALTRIALS_STATISTICS_URL = 'https://clinicaltrials.gov/api/info/study_statistics'
    response = requests.get(CLINICALTRIALS_STATISTICS_URL, params={'fmt': 'json'})
    studies_num = int(response.json()['StudyStatistics']['ElmtDefs']['Study']['nInstances'])
    return studies_num

def get_studies(start, end, sleep_count = 0):
    """
    clinicaltrials.gov 에서 제공하는 API 에서 임상 연구 목록을 가져오는 메소드
    """
    if sleep_count >= 10:
        raise ValidationError('clinicaltrials.gov API 요청 제한')
    
    CLINICALTRIALS_OPEN_API_BASE_URL = 'https://clinicaltrials.gov/api/query/full_studies'
    response = requests.get(CLINICALTRIALS_OPEN_API_BASE_URL, params={'fmt': 'json', 'min_rnk': start, 'max_rnk': end})
    
    if response.status_code == 404:
        raise ValidationError('clinicaltrials.gov API 응답 없음')

    if response.status_code == 401 or response.status_code == 403:
        sleep(600)
        get_studies(start, end, sleep_count+1)
    
    if response.status_code//100 == 5:
        sleep(60)
        get_studies(start, end, sleep_count+1)

    response_json = response.json()
    if response_json['FullStudiesResponse']['NStudiesFound'] == 0:
        return []
    return response_json['FullStudiesResponse']['FullStudies']

def convert_conditions(condition_module):
    conditions = []
    condition_instances = list(Condition.objects.filter(name__in=condition_module))
    for condition in condition_module:
        condition_id = None
        for condition_instance in condition_instances:
            if condition_instance.name == condition:
                condition_id = condition_instance.id
                break
        conditions.append({
            'id':  condition_id,
            'name': condition,
            'locale': 'en',
        })
    return conditions

def convert_interventions(study, intervention_module):
    interventions = []
    intervention_instances = list(Intervention.objects.filter(study=study))
    for intervention in intervention_module:
        intervention_id = None
        for intervention_instance in intervention_instances:
            if (
                intervention_instance.name == intervention.get('InterventionName', None) and \
                intervention_instance.intervention_type == intervention.get('InterventionType', None) and \
                intervention_instance.description == intervention.get('InterventionDescription', None)
            ):
                intervention_id = intervention_instance.pk
                intervention_instances.remove(intervention_instance)
                break
        interventions.append({
            'id': intervention_id,
            'intervention_type': intervention.get('InterventionType', None),
            'name': intervention.get('InterventionName', None),
            'description': intervention.get('InterventionDescription', None),
            'locale': 'en',
        })
    return interventions

def convert_eligibilities(study, eligibility_module):
    if eligibility_module is None:
        return []
    eligibility_instances = list(Eligibility.objects.filter(study=study))
    eligibility_id = None
    for eligibility_instance in eligibility_instances:
        if (
            eligibility_instance.gender == eligibility_module.get('Gender', None) and \
            eligibility_instance.minimum_age == eligibility_module.get('MinimumAge', None) and \
            eligibility_instance.maximum_age == eligibility_module.get('MaximumAge', None) and \
            eligibility_instance.healthy_volunteers == eligibility_module.get('HealthyVolunteers', None) and \
            eligibility_instance.criteria == eligibility_module.get('EligibilityCriteria', None)
        ):
            eligibility_id = eligibility_instance.pk
            eligibility_instances.remove(eligibility_instance)
            break
    return [{
        'id': eligibility_id,
        'gender': eligibility_module.get('Gender', None),
        'minimum_age': eligibility_module.get('MinimumAge', None),
        'maximum_age': eligibility_module.get('MaximumAge', None),
        'healthy_volunteers': eligibility_module.get('HealthyVolunteers', None),
        'criteria': eligibility_module.get('EligibilityCriteria', None),
        'locale': 'en',
    }]

def mark_updated_sutdy_field(study, convert_data):
    translated_studies = Study.objects.filter(translate_from_study=study)
    for field in TRANSLATE_FIELDS:
        if getattr(study, field) != convert_data[field]:
            for translated_study in translated_studies:
                setattr(translated_study, field, "<updated>")
    for translated_study in translated_studies:
        translated_study.save()

def convert_study(study):
    original_data = study.original_data
    if type(original_data) is not dict:
        original_data = json.loads(original_data)
    description_module = original_data['Study']['ProtocolSection'].get('DescriptionModule', {})

    if 'OfficialTitle' in description_module:
        title = description_module['OfficialTitle']
    elif 'BriefTitle' in description_module:
        title = description_module['BriefTitle']
    elif 'BriefSummary' in description_module:
        title = description_module['BriefSummary']
    else:
        title = None

    convert_data = {
        'nct_id': original_data['Study']['ProtocolSection']['IdentificationModule']['NCTId'],
        'title': title,
        'results_first_submitted_date': description_module.get('ResultsFirstSubmittedDate', None),
        'last_update_submitted_date': description_module.get('LastUpdateSubmittedDate', None),
        'start_date': description_module.get('StartDate', None),
        'completion_date': description_module.get('CompletionDate', None),
        'overall_status': description_module.get('OverallStatus', None),
        'phase': description_module.get('Phase', None),
        'enrollment': description_module.get('Enrollment', None),
        'interventions': convert_interventions(study, original_data['Study']['ProtocolSection'].get('ArmsInterventionsModule', {}).get('InterventionList', {}).get('Intervention', [])),
        'conditions': convert_conditions(original_data['Study']['ProtocolSection'].get('ConditionsModule', {}).get('ConditionList', {}).get('Condition', [])),
        'eligibilities': convert_eligibilities(study, original_data['Study']['ProtocolSection'].get('EligibilityModule', None)),
        'locale': 'en',
        'translate_from_study': None,
        'control_status_type': ControlStatusType.TRANSLATE_READY,
    }
    mark_updated_sutdy_field(study, convert_data)
    return convert_data

def translate(text):
    if text is None:
        return None
    translator = Translator(to_lang='ko')
    return translator.translate(text)

def translate_study(study, translated_study=None):
    """
    임상 연구 데이터를 번역하는 메소드
    """
    translated_text_dict = {translate_field:None for translate_field in TRANSLATE_FIELDS}
    if translated_study is not None:
        for translate_field in TRANSLATE_FIELDS:
            if getattr(translated_study, translate_field) != "<updated>":
                translated_text_dict[translate_field] = getattr(translated_study, translate_field)
    for translate_field in TRANSLATE_FIELDS:
        if translated_text_dict[translate_field] is None and getattr(study, translate_field) is not None:
            translated_text_dict[translate_field] = translate(getattr(study, translate_field))

    conditions = []
    for condition in study.conditions.all().prefetch_related(Prefetch("translated_conditions", queryset=Condition.objects.filter(locale='ko'))):
        translated_condition = condition.translated_conditions.first()
        if translated_condition is not None:
            conditions.append({
                'id': translated_condition.pk,
                'name': translated_condition.name,
                'locale': 'ko',
                'translate_from_condition': condition.pk
            })
        else:
            conditions.append({
                'name': translate(condition.name),
                'locale': 'ko',
                'translate_from_condition': condition.pk
            })

    interventions = []
    for intervention in Intervention.objects.filter(study=study).prefetch_related(Prefetch("translated_interventions", queryset=Intervention.objects.filter(locale='ko'))):
        translated_intervention = intervention.translated_interventions.first()
        if translated_intervention is not None:
            interventions.append({
                'id': translated_intervention.pk,
                'intervention_type': translated_intervention.intervention_type,
                'name': translated_intervention.name,
                'description': translated_intervention.description,
                'locale': 'ko',
                'translate_from_intervention': intervention.pk
            })
        else:
            interventions.append({
                'intervention_type': translate(intervention.intervention_type),
                'name': translate(intervention.name),
                'description': translate(intervention.description),
                'locale': 'ko',
                'translate_from_intervention': intervention.pk
            })

    eligibilities = []
    for eligibility in Eligibility.objects.filter(study=study).prefetch_related(Prefetch("translated_eligibilities", queryset=Eligibility.objects.filter(locale='ko'))):
        translated_eligibility = eligibility.translated_eligibilities.first()
        if translated_eligibility is not None:
            eligibilities.append({
                'id': translated_eligibility.pk,
                'gender': translated_eligibility.gender,
                'minimum_age': translated_eligibility.minimum_age,
                'maximum_age': translated_eligibility.maximum_age,
                'healthy_volunteers': translated_eligibility.healthy_volunteers,
                'criteria': translated_eligibility.criteria,
                'locale': 'ko',
                'translate_from_eligibility': eligibility.pk
            })
        else:
            eligibilities.append({
                'gender': translate(eligibility.gender),
                'minimum_age': eligibility.minimum_age,
                'maximum_age': eligibility.maximum_age,
                'healthy_volunteers': translate(eligibility.healthy_volunteers),
                'criteria': translate(eligibility.criteria),
                'locale': 'ko',
                'translate_from_eligibility': eligibility.pk
            })

    return {
        'nct_id': study.nct_id,
        'title': translated_text_dict['title'],
        'results_first_submitted_date': study.results_first_submitted_date,
        'last_update_submitted_date': study.last_update_submitted_date,
        'start_date': study.start_date,
        'completion_date': study.completion_date,
        'overall_status': translated_text_dict['overall_status'],
        'phase': translated_text_dict['phase'],
        'enrollment': study.enrollment,
        'interventions': interventions,
        'conditions': conditions,
        'eligibilities': eligibilities,
        'locale': 'ko',
        'translate_from_study': study.pk,
        'control_status_type': ControlStatusType.COMPLETED,
    }

def save_all_studies():
    """
    clinicaltrials.gov 에서 제공하는 API 에서 전체 임상 연구 목록을 저장하는 메소드
    """
    studies_num = get_studies_num()
    loaded_studies_num = int(ConfigurationVariable.objects.get_or_create(name='loaded_studies_num', defaults={'value': 1})[0].value)
    with tqdm(total=studies_num, initial=loaded_studies_num) as progress_bar:
        for start in range(loaded_studies_num, studies_num, 100):
            end = start + 99
            studies = get_studies(start, end)
            for original_data in studies:
                # save
                nct_id = get_nct_id(original_data)
                study = Study.objects.filter(nct_id=nct_id).first()
                original_data = json.dumps(original_data)
                original_data_hash = get_original_data_hash(original_data)
                with transaction.atomic():
                    if study is None:
                        study = Study(original_data=original_data, control_status_type=ControlStatusType.CONVERT_READY, original_data_hash=original_data_hash, nct_id=nct_id)
                        study.save()
                    elif study.original_data_hash != original_data_hash and not Study.objects.filter(clone_from_study=study).exists():
                        study = Study.objects.get(nct_id=get_nct_id(original_data), translate_from_study__isnull=True).clone()
                        study.original_data = original_data
                        study.original_data_hash = original_data_hash
                        study.control_status_type = ControlStatusType.CONVERT_READY
                        study.save()
                    else:
                        progress_bar.update(1)
                        ConfigurationVariable.objects.filter(name='loaded_studies_num').update(value=progress_bar.n)
                        continue
                try:
                    # convert
                    with transaction.atomic():
                        study_serializer = StudySerializer(data=convert_study(study), instance=study)
                        study_serializer.is_valid(raise_exception=True)
                        study_serializer.save()

                    # translate
                    with transaction.atomic():
                        translated_study_serializer = StudySerializer(data=translate_study(study))
                        translated_study_serializer.is_valid(raise_exception=True)
                        translated_study_serializer.save()
                        study.control_status_type = ControlStatusType.COMPLETED
                        study.save()
                except ValidationError as e:
                    if e.detail.get('nct_id', None) is not None and e.detail['nct_id'][0].code == 'unique':
                        continue
                    raise e
                finally:
                    progress_bar.update(1)
                    ConfigurationVariable.objects.filter(name='loaded_studies_num').update(value=progress_bar.n)
    ConfigurationVariable.objects.filter(name='loaded_studies_num').update(value=1)

def convert_studies():
    """
    저장된 original_data를 이용하여 임상 연구 데이터를 저장하는 메소드
    """
    studies_count = Study.objects.filter(control_status_type=ControlStatusType.CONVERT_READY).count()
    with tqdm(total=studies_count) as progress_bar:
        for study in Study.objects.filter(control_status_type=ControlStatusType.CONVERT_READY)[:100]:
            with transaction.atomic():
                try:
                    study_serializer = StudySerializer(data=convert_study(study), instance=study)
                    study_serializer.is_valid(raise_exception=True)
                    study_serializer.save()
                except:
                    traceback.print_exc()
                finally:
                    progress_bar.update(1)

def translate_studies():
    """
    저장된 임상 연구 데이터를 번역하는 메소드
    """
    studies_count = Study.objects.filter(control_status_type=ControlStatusType.TRANSLATE_READY).count()
    with tqdm(total=studies_count) as progress_bar:
        for study in Study.objects.filter(control_status_type=ControlStatusType.TRANSLATE_READY)[:100]:
            with transaction.atomic():
                try:
                    translated_study = study.translated_studies.filter(locale='ko').first()
                    if translated_study is None:
                        translated_study_serializer = StudySerializer(data=translate_study(study))
                    else:
                        translated_study_serializer = StudySerializer(data=translate_study(study, translated_study), instance=translated_study)
                    translated_study_serializer.is_valid(raise_exception=True)
                    translated_study_serializer.save()
                    study.control_status_type = ControlStatusType.COMPLETED
                    study.save()
                except:
                    traceback.print_exc()
                finally:
                    progress_bar.update(1)

def save_all_new_studies():
    """
    clinicaltrials.gov 에서 제공하는 API 에서 전체 임상 연구 중 신규 임상을 저장하는 메소드
    """
    studies_num = get_studies_num()
    loaded_new_studies_num = int(ConfigurationVariable.objects.get_or_create(name='loaded_new_studies_num', defaults={'value': 1})[0].value)
    with tqdm(total=studies_num, initial=loaded_new_studies_num) as progress_bar:
        for start in range(1, studies_num, 100):
            end = start + 99
            studies = get_studies(start, end)
            for original_data in studies:
                # save
                with transaction.atomic():
                    if Study.objects.filter(nct_id=get_nct_id(original_data)).exists():
                        progress_bar.update(1)
                        ConfigurationVariable.objects.filter(name='loaded_new_studies_num').update(value=progress_bar.n)
                        continue
                    nct_id = get_nct_id(original_data)
                    original_data = json.dumps(original_data)
                    study = Study(original_data=original_data, control_status_type=ControlStatusType.CONVERT_READY, original_data_hash=get_original_data_hash(original_data), nct_id=nct_id)
                    study.save()
                try:
                    # convert
                    with transaction.atomic():
                        study_serializer = StudySerializer(data=convert_study(study), instance=study)
                        study_serializer.is_valid(raise_exception=True)
                        study_serializer.save()

                    # translate
                    with transaction.atomic():
                        translated_study_serializer = StudySerializer(data=translate_study(study))
                        translated_study_serializer.is_valid(raise_exception=True)
                        translated_study_serializer.save()
                        study.control_status_type = ControlStatusType.COMPLETED
                        study.save()
                except:
                    traceback.print_exc()
                finally:
                    progress_bar.update(1)
                    ConfigurationVariable.objects.filter(name='loaded_new_studies_num').update(value=progress_bar.n)

    ConfigurationVariable.objects.filter(name='loaded_new_studies_num').update(value=1)
def save_new_study_original_datas():
    """
    clinicaltrials.gov 에서 제공하는 API 에서 신규 임상 연구 데이터를 저장하는 메소드
    """
    studies_num = get_studies_num()
    loaded_new_studies_num = int(ConfigurationVariable.objects.get_or_create(name='loaded_new_studies_num', defaults={'value': 1})[0].value)
    with tqdm(total=studies_num, initial=loaded_new_studies_num) as progress_bar:
        for start in range(1, studies_num, 100):
            end = start + 99
            studies = get_studies(start, end)
            for original_data in studies:
                if Study.objects.filter(nct_id=get_nct_id(original_data)).exists():
                    progress_bar.update(1)
                    ConfigurationVariable.objects.filter(name='loaded_new_studies_num').update(value=progress_bar.n)
                    continue
                nct_id = get_nct_id(original_data)
                original_data = get_original_data_hash(original_data)
                study = Study(original_data=original_data, control_status_type=ControlStatusType.CONVERT_READY, original_data_hash=get_original_data_hash(original_data), nct_id=nct_id)
                study.save()
                progress_bar.update(1)
                ConfigurationVariable.objects.filter(name='loaded_new_studies_num').update(value=progress_bar.n)

    ConfigurationVariable.objects.filter(name='loaded_new_studies_num').update(value=1)

def update_study_original_data():
    """
    clinicaltrials.gov 에서 제공하는 API 에서 임상 연구 데이터를 업데이트 하는 메소드
    """
    studies_num = get_studies_num()
    updated_studies_num = int(ConfigurationVariable.objects.get_or_create(name='updated_studies_num', defaults={'value': 1})[0].value)
    with tqdm(total=studies_num, initial=updated_studies_num) as progress_bar:
        for start in range(1, studies_num, 100):
            end = start + 99
            studies = get_studies(start, end)
            for original_data in studies:
                original_study = Study.objects.filter(nct_id=get_nct_id(original_data), translate_from_study__isnull=True).first()
                original_data = json.dumps(original_data)
                original_data_hash = get_original_data_hash(original_data)
                if original_study is not None and original_study.original_data_hash != original_data_hash and not Study.objects.filter(clone_from_study=original_study).exists():
                    study = original_study.clone()
                    study.original_data = original_data
                    study.original_data_hash = original_data_hash
                    study.control_status_type = ControlStatusType.CONVERT_READY
                    study.save()
                progress_bar.update(1)
                ConfigurationVariable.objects.filter(name='updated_studies_num').update(value=progress_bar.n)

    ConfigurationVariable.objects.filter(name='updated_studies_num').update(value=1)
