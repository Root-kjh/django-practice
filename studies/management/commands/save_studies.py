from django.core.management.base import BaseCommand
from studies.batch_tasks import save_all_studies
class Command(BaseCommand):
    help = 'clinicaltrials.gov의 전체 임상연구 적재'

    def handle(self, *args, **options):
        save_all_studies()