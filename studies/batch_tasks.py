import requests
from rest_framework.exceptions import ValidationError
from tqdm import tqdm
from time import sleep
from translate import Translator
from django.db import transaction
import traceback

from .models import ConfigurationVariable, Study
from .assets import ControlStatusType
from .serializers import StudySerializer

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

def convert_study(study):
    description_module = study['Study']['ProtocolSection'].get('DescriptionModule', {})

    if 'OfficialTitle' in description_module:
        title = description_module['OfficialTitle']
    elif 'BriefTitle' in description_module:
        title = description_module['BriefTitle']
    elif 'BriefSummary' in description_module:
        title = description_module['BriefSummary']
    else:
        title = None

    interventions = study['Study']['ProtocolSection'].get('ArmsInterventionsModule', {}).get('InterventionList', {}).get('Intervention', [])
    conditions = study['Study']['ProtocolSection'].get('ConditionsModule', {}).get('ConditionList', {}).get('Condition', [])
    eligibility_module = study['Study']['ProtocolSection'].get('EligibilityModule', None)
    if eligibility_module is None:
        eligibility = []
    else:
        eligibility = [
            {
                'gender': eligibility_module.get('Gender', None),
                'minimum_age': eligibility_module.get('MinimumAge', None),
                'maximum_age': eligibility_module.get('MaximumAge', None),
                'healthy_volunteers': eligibility_module.get('HealthyVolunteers', None),
                'criteria': eligibility_module.get('EligibilityCriteria', None),
                'locale': 'en',
            }
        ]
    return {
        'nct_id': study['Study']['ProtocolSection']['IdentificationModule']['NCTId'],
        'title': title,
        'results_first_submitted_date': description_module.get('ResultsFirstSubmittedDate', None),
        'last_update_submitted_date': description_module.get('LastUpdateSubmittedDate', None),
        'start_date': description_module.get('StartDate', None),
        'completion_date': description_module.get('CompletionDate', None),
        'overall_status': description_module.get('OverallStatus', None),
        'phase': description_module.get('Phase', None),
        'enrollment': description_module.get('Enrollment', None),
        'interventions': [
            {
                'intervention_type': intervention.get('InterventionType', None),
                'name': intervention.get('InterventionName', None),
                'description': intervention.get('InterventionDescription', None),
                'locale': 'en',
            }
            for intervention in interventions
        ],
        'conditions': [
            {
                'name': condition,
                'locale': 'en',
            }
            for condition in conditions
        ],
        'eligibilities': eligibility,
        'locale': 'en',
        'original_study': None,
        'control_status_type': ControlStatusType.TRANSLATE_READY,
    }

def translate(text):
    if text is None:
        return None
    translator = Translator(to_lang='ko')
    return translator.translate(text)

def translate_study(study):
    """
    임상 연구 데이터를 번역하는 메소드
    """
    return {
        'nct_id': study.nct_id,
        'title': translate(study.title),
        'results_first_submitted_date': study.results_first_submitted_date,
        'last_update_submitted_date': study.last_update_submitted_date,
        'start_date': study.start_date,
        'completion_date': study.completion_date,
        'overall_status': translate(study.overall_status),
        'phase': translate(study.phase),
        'enrollment': study.enrollment,
        'interventions': [
            {
                'intervention_type': translate(intervention.intervention_type),
                'name': translate(intervention.name),
                'description': translate(intervention.description),
                'locale': 'ko',
                'original_intervention': intervention.pk
            }
            for intervention in study.interventions.all()
        ],
        'conditions': [
            {
                'name': translate(condition.name),
                'locale': 'ko',
                'original_condition': condition.pk
            }
            for condition in study.conditions.all()
        ],
        'eligibilities': [
            {
                'gender': translate(eligibility.gender),
                'minimum_age': eligibility.minimum_age,
                'maximum_age': eligibility.maximum_age,
                'healthy_volunteers': translate(eligibility.healthy_volunteers),
                'criteria': translate(eligibility.criteria),
                'locale': 'ko',
                'original_eligibility': eligibility.pk
            }
            for eligibility in study.eligibilities.all()
        ],
        'locale': 'ko',
        'original_study': study.pk,
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
                with transaction.atomic():
                    study = Study(original_data=original_data, control_status_type=ControlStatusType.CONVERT_READY)
                    study.save()
                try:
                    # convert
                    with transaction.atomic():
                        study_serializer = StudySerializer(data=convert_study(original_data), instance=study)
                        study_serializer.is_valid(raise_exception=True)
                        study_serializer.save()

                    # translate
                    with transaction.atomic():
                        translated_study_serializer = StudySerializer(data=translate_study(study_serializer.instance))
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

def save_study_original_datas():
    """
    clinicaltrials.gov 에서 제공하는 API 에서 임상 연구 데이터를 저장하는 메소드
    """
    studies_num = get_studies_num()
    loaded_studies_num = int(ConfigurationVariable.objects.get_or_create(name='loaded_studies_num', defaults={'value': 1})[0].value)
    with tqdm(total=studies_num, initial=loaded_studies_num) as progress_bar:
        for start in range(loaded_studies_num, studies_num, 100):
            end = start + 99
            studies = get_studies(start, end)
            for original_data in studies:
                study = Study(original_data=original_data, control_status_type=ControlStatusType.CONVERT_READY)
                study.save()
                progress_bar.update(1)
                ConfigurationVariable.objects.filter(name='loaded_studies_num').update(value=progress_bar.n)

def convert_studies():
    """
    저장된 original_data를 이용하여 임상 연구 데이터를 저장하는 메소드
    """
    studies_count = Study.objects.filter(control_status_type=ControlStatusType.CONVERT_READY).count()
    with tqdm(total=studies_count) as progress_bar:
        for study in Study.objects.filter(control_status_type=ControlStatusType.CONVERT_READY)[:100]:
            with transaction.atomic():
                try:
                    study_serializer = StudySerializer(data=convert_study(study.original_data), instance=study)
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
                    translated_study_serializer = StudySerializer(data=translate_study(study))
                    translated_study_serializer.is_valid(raise_exception=True)
                    translated_study_serializer.save()
                    study.control_status_type = ControlStatusType.COMPLETED
                    study.save()
                except:
                    traceback.print_exc()
                finally:
                    progress_bar.update(1)

