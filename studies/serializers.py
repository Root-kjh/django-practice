from rest_framework.serializers import ModelSerializer
from drf_writable_nested.serializers import WritableNestedModelSerializer

from .models import Study, Intervention, Condition, Eligibility

class InterventionSerializer(ModelSerializer):
    class Meta:
        model = Intervention
        fields = ['intervention_type', 'name', 'description', 'original_intervention', 'locale']


class ConditionSerializer(ModelSerializer):
    class Meta:
        model = Condition
        fields = ['name', 'original_condition', 'locale']


class EligibilitySerializer(ModelSerializer):
    class Meta:
        model = Eligibility
        fields = ['gender', 'minimum_age', 'maximum_age', 'healthy_volunteers', 'criteria', 'original_eligibility', 'locale']


class StudySerializer(WritableNestedModelSerializer):
    interventions = InterventionSerializer(many=True)
    conditions = ConditionSerializer(many=True)
    eligibilities = EligibilitySerializer(many=True)

    class Meta:
        model = Study
        fields = '__all__'

