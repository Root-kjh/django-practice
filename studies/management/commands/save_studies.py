from enum import Enum
from django.core.management.base import BaseCommand
from studies.batch_tasks import save_all_studies, convert_studies, translate_studies, save_study_original_datas, save_all_new_studies, save_new_study_original_datas, update_study_original_data

class CommandAction(Enum):
    SAVE_ALL_STUDIES = "save_all_studies"
    CONVERT = "convert"
    TRANSLATE = "translate"
    SAVE_ALL_NEW_STUDIES = "save_all_new_studies"
    SAVE_NEW_ORIGINAL_DATA = "save_new_original_data"
    UPDATE_ORIGINAL_DATA = "update_original_data"


class Command(BaseCommand):
    help = 'clinicaltrials.gov의 전체 임상연구 적재'

    actions = {
        CommandAction.SAVE_ALL_STUDIES: save_all_studies,
        CommandAction.CONVERT: convert_studies,
        CommandAction.TRANSLATE: translate_studies,
        CommandAction.SAVE_ALL_NEW_STUDIES: save_all_new_studies,
        CommandAction.SAVE_NEW_ORIGINAL_DATA: save_new_study_original_datas,
        CommandAction.UPDATE_ORIGINAL_DATA: update_study_original_data,
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--save-all-studies",
            action="store_const",
            dest="action",
            const=CommandAction.SAVE_ALL_STUDIES,
            help="save all studies",
        )
        parser.add_argument(
            "--convert",
            action="store_const",
            dest="action",
            const=CommandAction.CONVERT,
            help="convert original data",
        )
        parser.add_argument(
            "--translate",
            action="store_const",
            dest="action",
            const=CommandAction.TRANSLATE,
            help="translate study",
        )
        parser.add_argument(
            "--save-all-new-studies",
            action="store_const",
            dest="action",
            const=CommandAction.SAVE_ALL_NEW_STUDIES,
            help="save all new studies",
        )
        parser.add_argument(
            "--save-new-original-data",
            action="store_const",
            dest="action",
            const=CommandAction.SAVE_NEW_ORIGINAL_DATA,
            help="save new original data",
        )
        parser.add_argument(
            "--update-original-data",
            action="store_const",
            dest="action",
            const=CommandAction.UPDATE_ORIGINAL_DATA,
            help="update original data",
        )


    def handle(self, *args, **options):
        self.actions[options["action"]]()