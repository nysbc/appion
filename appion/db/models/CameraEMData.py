from django.db import models
from .SessionData import SessionData
from .InstrumentData import InstrumentData

class CameraEMData(models.Model):
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
    system_time = models.FloatField(
        db_column="system time", blank=True, null=True
    )
    subd_dimension_x = models.IntegerField(
        db_column="SUBD|dimension|x", blank=True, null=True
    )
    subd_dimension_y = models.IntegerField(
        db_column="SUBD|dimension|y", blank=True, null=True
    )
    subd_binning_x = models.IntegerField(
        db_column="SUBD|binning|x", blank=True, null=True
    )
    subd_binning_y = models.IntegerField(
        db_column="SUBD|binning|y", blank=True, null=True
    )
    binned_multiplier = models.FloatField(
        db_column="binned multiplier", blank=True, null=True
    )
    subd_offset_x = models.IntegerField(
        db_column="SUBD|offset|x", blank=True, null=True
    )
    subd_offset_y = models.IntegerField(
        db_column="SUBD|offset|y", blank=True, null=True
    )
    exposure_time = models.FloatField(
        db_column="exposure time", blank=True, null=True
    )
    exposure_type = models.TextField(
        db_column="exposure type", blank=True, null=True
    )
    exposure_timestamp = models.FloatField(
        db_column="exposure timestamp", blank=True, null=True
    )
    intensity_averaged = models.BooleanField(
        db_column="intensity averaged", blank=True, null=True
    )
    inserted = models.BooleanField(blank=True, null=True)
    dump = models.BooleanField(blank=True, null=True)
    subd_pixel_size_x = models.FloatField(
        db_column="SUBD|pixel size|x", blank=True, null=True
    )
    subd_pixel_size_y = models.FloatField(
        db_column="SUBD|pixel size|y", blank=True, null=True
    )
    energy_filtered = models.BooleanField(
        db_column="energy filtered", blank=True, null=True
    )
    energy_filter = models.BooleanField(
        db_column="energy filter", blank=True, null=True
    )
    energy_filter_width = models.FloatField(
        db_column="energy filter width", blank=True, null=True
    )
    nframes = models.IntegerField(blank=True, null=True)
    save_frames = models.BooleanField(
        db_column="save frames", blank=True, null=True
    )
    align_frames = models.BooleanField(
        db_column="align frames", blank=True, null=True
    )
    tiff_frames = models.BooleanField(
        db_column="tiff frames", blank=True, null=True
    )
    eer_frames = models.BooleanField(
        db_column="eer frames", blank=True, null=True
    )
    align_filter = models.TextField(
        db_column="align filter", blank=True, null=True
    )
    frames_name = models.TextField(
        db_column="frames name", blank=True, null=True
    )
    seq_use_frames = models.TextField(
        db_column="SEQ|use frames", blank=True, null=True
    )
    frame_time = models.FloatField(
        db_column="frame time", blank=True, null=True
    )
    frame_flip = models.IntegerField(
        db_column="frame flip", blank=True, null=True
    )
    frame_rotate = models.IntegerField(
        db_column="frame rotate", blank=True, null=True
    )
    temperature = models.FloatField(blank=True, null=True)
    temperature_status = models.TextField(
        db_column="temperature status", blank=True, null=True
    )
    readout_delay = models.IntegerField(
        db_column="readout delay", blank=True, null=True
    )
    gain_index = models.IntegerField(
        db_column="gain index", blank=True, null=True
    )
    system_corrected = models.BooleanField(
        db_column="system corrected", blank=True, null=True
    )
    ref_instrumentdata_ccdcamera = models.ForeignKey(
        InstrumentData,
        db_column="REF|InstrumentData|ccdcamera",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    request_nframes = models.IntegerField(
        db_column="request nframes", blank=True, null=True
    )
    sum_gain_corrected = models.BooleanField(
        db_column="sum gain corrected", blank=True, null=True
    )
    frame_gain_corrected = models.BooleanField(
        db_column="frame gain corrected", blank=True, null=True
    )
    system_dark_subtracted = models.BooleanField(
        db_column="system dark subtracted", blank=True, null=True
    )
    use_cds = models.BooleanField(
        db_column="use cds", blank=True, null=True
    )
    fast_save = models.BooleanField(
        db_column="fast save", blank=True, null=True
    )

    def __str__(self) -> str:
        session = "<no session>"
        if s := self.ref_sessiondata_session:
            session = s.name
        return "%s|%s" % (session, self.def_timestamp)

    class Meta:
        managed = False
        verbose_name = "CameraEMData"
        verbose_name_plural = "CameraEMData"
        db_table = "CameraEMData"


