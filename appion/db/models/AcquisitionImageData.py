from django.db import models
from .SessionData import SessionData
from .CameraEMData import CameraEMData
from .CorrectorPlanData import CorrectorPlanData
from .PresetData import PresetData
from .ScopeEMData import ScopeEMData

class AcquisitionImageData(models.Model):
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
    mrc_image = models.TextField(db_column="MRC|image", blank=True, null=True)
    pixeltype = models.TextField(blank=True, null=True)
    pixels = models.IntegerField(blank=True, null=True)
    label = models.TextField(blank=True, null=True)
    filename = models.TextField(blank=True, null=True)
    ref_imagelistdata_list = models.IntegerField(
        db_column="REF|ImageListData|list", blank=True, null=True
    )
    ref_queuedata_queue = models.IntegerField(
        db_column="REF|QueueData|queue", blank=True, null=True
    )
    ref_scopeemdata_scope = models.ForeignKey(
        ScopeEMData,
        db_column="REF|ScopeEMData|scope",
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
    ref_correctorplandata_corrector_plan = models.ForeignKey(
        CorrectorPlanData,
        db_column="REF|CorrectorPlanData|corrector plan",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    correction_channel = models.IntegerField(
        db_column="correction channel", blank=True, null=True
    )
    channel = models.IntegerField(blank=True, null=True)
    ref_darkimagedata_dark = models.IntegerField(
        db_column="REF|DarkImageData|dark", blank=True, null=True
    )
    ref_brightimagedata_bright = models.IntegerField(
        db_column="REF|BrightImageData|bright", blank=True, null=True
    )
    ref_normimagedata_norm = models.IntegerField(
        db_column="REF|NormImageData|norm", blank=True, null=True
    )
    ref_presetdata_preset = models.ForeignKey(
        PresetData,
        db_column="REF|PresetData|preset",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    ref_acquisitionimagetargetdata_target = models.IntegerField(
        db_column="REF|AcquisitionImageTargetData|target", blank=True, null=True
    )
    ref_emtargetdata_emtarget = models.IntegerField(
        db_column="REF|EMTargetData|emtarget", blank=True, null=True
    )
    ref_griddata_grid = models.IntegerField(
        db_column="REF|GridData|grid", blank=True, null=True
    )
    ref_spotwellmapdata_spotmap = models.IntegerField(
        db_column="REF|SpotWellMapData|spotmap", blank=True, null=True
    )
    ref_tiltseriesdata_tilt_series = models.IntegerField(
        db_column="REF|TiltSeriesData|tilt series", blank=True, null=True
    )
    version = models.IntegerField(blank=True, null=True)
    tiltnumber = models.IntegerField(blank=True, null=True)
    ref_moverparamsdata_mover = models.IntegerField(
        db_column="REF|MoverParamsData|mover", blank=True, null=True
    )
    seq_use_frames = models.TextField(
        db_column="SEQ|use frames", blank=True, null=True
    )

    def __str__(self) -> str:
        return self.mrc_image or "<no mrc>"

    class Meta:
        managed = False
        verbose_name = "AcquisitionImageData"
        verbose_name_plural = "AcquisitionImageData"
        db_table = "AcquisitionImageData"
