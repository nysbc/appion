from django.db import models
from .InstrumentData import InstrumentData
from .SessionData import SessionData

class PresetData(models.Model):
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
    number = models.IntegerField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    skip = models.BooleanField(blank=True, null=True)
    removed = models.BooleanField(blank=True, null=True)
    hasref = models.BooleanField(blank=True, null=True)
    ref_instrumentdata_tem = models.ForeignKey(
        InstrumentData,
        db_column="REF|InstrumentData|tem",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    projection_mode = models.TextField(db_column="projection mode", blank=True, null=True)
    magnification = models.IntegerField(blank=True, null=True)
    spot_size = models.IntegerField(db_column="spot size", blank=True, null=True)
    intensity = models.FloatField(blank=True, null=True)
    image_shift_x = models.FloatField(db_column="SUBD|image shift|x", blank=True, null=True)
    image_shift_y = models.FloatField(db_column="SUBD|image shift|y", blank=True, null=True)
    beam_shift_x = models.FloatField(db_column="SUBD|beam shift|x", blank=True, null=True)
    beam_shift_y = models.FloatField(db_column="SUBD|beam shift|y", blank=True, null=True)
    diffraction_shift_x = models.FloatField(db_column="SUBD|diffraction shift|x", blank=True, null=True)
    diffraction_shift_y = models.FloatField(db_column="SUBD|diffraction shift|y", blank=True, null=True)
    defocus = models.FloatField(blank=True, null=True)
    defocus_range_min = models.FloatField(db_column="defocus range min", blank=True, null=True)
    defocus_range_max = models.FloatField(db_column="defocus range max", blank=True, null=True)
    dose = models.FloatField(blank=True, null=True)
    tem_energy_filter = models.BooleanField(db_column="tem energy filter", blank=True, null=True)
    tem_energy_filter_width = models.FloatField(db_column="tem energy filter width", blank=True, null=True)
    probe_mode = models.TextField(db_column="probe mode", blank=True, null=True)
    ref_instrumentdata_ccdcamera = models.ForeignKey(
        InstrumentData,
        db_column="REF|InstrumentData|ccdcamera",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    exposure_time = models.FloatField(db_column="exposure time", blank=True, null=True)
    dimension_x = models.IntegerField(db_column="SUBD|dimension|x", blank=True, null=True)
    dimension_y = models.IntegerField(db_column="SUBD|dimension|y", blank=True, null=True)
    binning_x = models.IntegerField(db_column="SUBD|binning|x", blank=True, null=True)
    binning_y = models.IntegerField(db_column="SUBD|binning|y", blank=True, null=True)
    offset_x = models.IntegerField(db_column="SUBD|offset|x", blank=True, null=True)
    offset_y = models.IntegerField(db_column="SUBD|offset|y", blank=True, null=True)
    energy_filter = models.BooleanField(db_column="energy filter", blank=True, null=True)
    energy_filter_width = models.FloatField(db_column="energy filter width", blank=True, null=True)
    energy_filter_offset = models.FloatField(db_column="energy filter offset", blank=True, null=True)
    pre_exposure = models.FloatField(db_column="pre exposure", blank=True, null=True)
    alt_channel = models.BooleanField(db_column="alt channel", blank=True, null=True)
    save_frames = models.BooleanField(db_column="save frames", blank=True, null=True)
    frame_time = models.FloatField(db_column="frame time", blank=True, null=True)
    request_nframes = models.IntegerField(db_column="request nframes", blank=True, null=True)
    align_frames = models.BooleanField(db_column="align frames", blank=True, null=True)
    align_filter = models.TextField(db_column="align filter", blank=True, null=True)
    use_frames = models.TextField(db_column="SEQ|use frames", blank=True, null=True)
    readout_delay = models.IntegerField(db_column="readout delay", blank=True, null=True)
    fast_save = models.BooleanField(db_column="fast save", blank=True, null=True)
    use_cds = models.BooleanField(db_column="use cds", blank=True, null=True) 
    class Meta:
        managed = False
        verbose_name = "PresetData"
        verbose_name_plural = "PresetData"
        db_table = "PresetData"