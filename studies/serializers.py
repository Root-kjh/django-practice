from rest_framework.serializers import ModelSerializer

from .models import Study, Intervention, Condition, Eligibility

class InterventionSerializer(ModelSerializer):
    class Meta:
        model = Intervention
        fields = ['intervention_type', 'name', 'description']


class ConditionSerializer(ModelSerializer):
    class Meta:
        model = Condition
        fields = ['name']


class EligibilitySerializer(ModelSerializer):
    class Meta:
        model = Eligibility
        fields = ['gender', 'minimum_age', 'maximum_age', 'healthy_volunteers', 'criteria']


class StudySerializer(ModelSerializer):
    interventions = InterventionSerializer(many=True, read_only=True)
    conditions = ConditionSerializer(many=True, read_only=True)
    eligibilities = EligibilitySerializer(many=True, read_only=True)

    class Meta:
        model = Study
        fields = '__all__'

