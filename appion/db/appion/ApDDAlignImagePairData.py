from django.db import models
from ..models import AcquisitionImageData
from ApDDStackRunData import ApDDStackRunData

class ApDDAlignImagePairData(models.Model):
    def_id = models.AutoField(db_column="DEF_id", primary_key=True)
    def_timestamp = models.DateTimeField(
        db_column="DEF_timestamp", auto_now_add=True
    )
    ref_acquisitionimagedata_source = models.ForeignKey(
        AcquisitionImageData,
        db_column="REF|AcquisitionImageData|source",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    ref_acquisitionimagedata_result = models.ForeignKey(
        AcquisitionImageData,
        db_column="REF|AcquisitionImageData|result",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    ref_apddstackrundata_ddstackrun = models.ForeignKey(
        ApDDStackRunData,
        db_column="REF|ApDDStackRunData|ddstackrun",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    class Meta:
        managed = False
        verbose_name = "ApDDAlignImagePairData"
        verbose_name_plural = "ApDDAlignImagePairData"
        db_table = "ApDDAlignImagePairData"