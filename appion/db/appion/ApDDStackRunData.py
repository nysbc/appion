from django.db import models
from ..models import SessionData
from ApDDStackParamsData import ApDDStackParamsData
from ApPathData import ApPathData

class ApDDStackRunData(models.Model):
    def_id = models.AutoField(db_column="DEF_id", primary_key=True)
    def_timestamp = models.DateTimeField(
        db_column="DEF_timestamp", auto_now_add=True
    )
    runname =  models.TextField(blank=True,null=True) 
    ref_apddstackparamsdata_params = models.ForeignKey(
        ApDDStackParamsData,
        db_column="REF|ApDDStackParamsData|params",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    ref_ApPathData_path = models.ForeignKey(
        ApPathData,
        db_column="REF|ApPathData|path",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    class Meta:
        managed = False
        verbose_name = "ApDDStackRunData"
        verbose_name_plural = "ApDDStackRunData"
        db_table = "ApDDStackRunData"