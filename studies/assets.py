from django.db import models

class ControlStatusType(models.IntegerChoices):
    CONVERT_READY = 20, 'CONVERT_READY'
    TRANSLATE_READY = 50, 'TRANSLATE_READY'
    COMPLETED = 100, 'COMPLETED'