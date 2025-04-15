from django.db import models
from .SessionData import SessionData
from .CameraEMData import CameraEMData

class CorrectorPlanData(models.Model):
    def_id = models.AutoField(db_column="DEF_id", primary_key=True)
    def_timestamp = models.DateTimeField(
        db_column="DEF_timestamp", auto_now_add=True
    )
    ref_sessiondata_session = models.ForeignKey(
        SessionData,
        db_column="REF|SessionData|session",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    ref_cameraemdata_camera = models.ForeignKey(
        CameraEMData,
        db_column="REF|CameraEMData|camera",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    bad_rows = models.TextField(db_column="SEQ|bad_rows", blank=True, null=True)
    bad_cols = models.TextField(db_column="SEQ|bad_cols", blank=True, null=True)
    bad_pixels = models.TextField(db_column="SEQ|bad_pixels", blank=True, null=True)
    #clip_limits = models.TextField(db_column="SEQ|clip_limits", blank=True, null=True)
    despike = models.BooleanField(blank=True, null=True)
    despike_size = models.IntegerField(db_column="despike size", blank=True, null=True)
    despike_threshold = models.FloatField(db_column="despike threshold", blank=True, null=True)
    class Meta:
        managed = False
        verbose_name = "CorrectorPlanData"
        verbose_name_plural = "CorrectorPlanData"
        db_table = "CorrectorPlanData"