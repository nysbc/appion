from django.db import models
from .SessionData import SessionData
from .InstrumentData import InstrumentData

class PixelSizeCalibrationData(models.Model):
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
    ref_instrumentdata_tem = models.ForeignKey(
        InstrumentData,
        db_column="REF|InstrumentData|tem",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    ref_instrumentdata_ccdcamera = models.ForeignKey(
        InstrumentData,
        db_column="REF|InstrumentData|ccdcamera",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    projection_mode = models.TextField(db_column="projection mode", blank=True, null=True)
    magnification = models.IntegerField(blank=True, null=True)
    high_tension = models.IntegerField(db_column="high tension", blank=True, null=True)
    pixelsize = models.FloatField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    class Meta:
        managed = False
        verbose_name = "PixelSizeCalibrationData"
        verbose_name_plural = "PixelSizeCalibrationData"
        db_table = "PixelSizeCalibrationData"

	