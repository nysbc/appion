from django.db import models
from ..models import AcquisitionImageData
from ApDDStackRunData import ApDDStackRunData
from ApDDFrameTrajectoryData import ApDDFrameTrajectoryData

class ApDDAlignStatsData(models.Model):
    def_id = models.AutoField(db_column="DEF_id", primary_key=True)
    def_timestamp = models.DateTimeField(
        db_column="DEF_timestamp", auto_now_add=True
    )
    ref_acquisitionimagedata_image = models.ForeignKey(
        AcquisitionImageData,
        db_column="REF|AcquisitionImageData|image",
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
    ref_apddframetrajectorydata_trajectory = models.ForeignKey(
        ApDDFrameTrajectoryData,
        db_column="REF|ApDDFrameTrajectoryData|trajectory",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    #angstroms per pixel
    apix = models.FloatField(blank=True,null=True) 
    #pixels
    top_shift1_value = models.FloatField(blank=True,null=True) 
    #pixels
    top_shift2_value = models.FloatField(blank=True,null=True)
    #pixels
    top_shift3_value = models.FloatField(blank=True,null=True) 
    #base-0
    top_shift1_index = models.IntegerField(blank=True,null=True)
    #base-0
    top_shift2_index = models.IntegerField(blank=True,null=True)
    #base-0
    top_shift3_index = models.IntegerField(blank=True,null=True)
    # pixels
    median_shift_value = models.FloatField(blank=True,null=True)
    class Meta:
        managed = False
        verbose_name = "ApDDAlignStatsData"
        verbose_name_plural = "ApDDAlignStatsData"
        db_table = "ApDDAlignStatsData"