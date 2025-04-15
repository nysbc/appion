from django.db import models
from ..models import SessionData
from ApDDStackParamsData import ApDDStackParamsData
from ApPathData import ApPathData

class ApPathData(models.Model):
    def_id = models.AutoField(db_column="DEF_id", primary_key=True)
    def_timestamp = models.DateTimeField(
        db_column="DEF_timestamp", auto_now_add=True
    )
    path = models.TextField(blank=True,null=True)
    class Meta:
        managed = False
        verbose_name = "ApPathData"
        verbose_name_plural = "ApPathData"
        db_table = "ApPathData"