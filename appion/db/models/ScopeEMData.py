from django.db import models
from .SessionData import SessionData
from .InstrumentData import InstrumentData

class ScopeEMData(models.Model):
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
    focus = models.FloatField(blank=True, null=True)
    reset_defocus = models.IntegerField(db_column="reset defocus", blank=True, null=True)
    screen_current = models.FloatField(db_column="screen current", blank=True, null=True) 
    beam_blank = models.TextField(db_column="beam blank", blank=True, null=True) 
    stigmator_condenser_x = models.FloatField(db_column="SUBD|stigmator|SUBD|condenser|x", blank=True, null=True)
    stigmator_condenser_y = models.FloatField(db_column="SUBD|stigmator|SUBD|condenser|y", blank=True, null=True)
    stigmator_diffraction_x = models.FloatField(db_column="SUBD|stigmator|SUBD|diffraction|x", blank=True, null=True) 
    stigmator_diffraction_y = models.FloatField(db_column="SUBD|stigmator|SUBD|diffraction|y", blank=True, null=True)
    stigmator_objective_y = models.FloatField(db_column="SUBD|stigmator|SUBD|objective|x", blank=True, null=True)
    stigmator_objective_z = models.FloatField(db_column="SUBD|stigmator|SUBD|objective|y", blank=True, null=True)
    beam_tilt_x = models.FloatField(db_column="SUBD|beam tilt|x", blank=True, null=True)
    beam_tilt_y = models.FloatField(db_column="SUBD|beam tilt|y", blank=True, null=True)
    corrected_stage_position = models.IntegerField(db_column="corrected stage position", blank=True, null=True)
    stage_position_a = models.FloatField(db_column="SUBD|stage position|a", blank=True, null=True)
    stage_position_b = models.FloatField(db_column="SUBD|stage position|b", blank=True, null=True)
    stage_position_x = models.FloatField(db_column="SUBD|stage position|x", blank=True, null=True)
    stage_position_y = models.FloatField(db_column="SUBD|stage position|y", blank=True, null=True)
    stage_position_z = models.FloatField(db_column="SUBD|stage position|z", blank=True, null=True)
    holder_type = models.TextField(db_column="holder type", blank=True, null=True)
    holder_status = models.TextField(db_column="holder status", blank=True, null=True)
    stage_status = models.TextField(db_column="stage status", blank=True, null=True)
    vacuum_status = models.TextField(db_column="vacuum status", blank=True, null=True)
    column_valves = models.TextField(db_column="column valves", blank=True, null=True)
    column_pressure = models.FloatField(db_column="column pressure", blank=True, null=True)
    turbo_pump = models.TextField(db_column="turbo pump", blank=True, null=True)
    high_tension = models.IntegerField(db_column="high tension", blank=True, null=True)
    main_screen_position = models.TextField(db_column="main screen position", blank=True, null=True)
    main_screen_magnification = models.IntegerField(db_column="main screen magnification", blank=True, null=True)
    small_screen_position = models.TextField(db_column="small screen position", blank=True, null=True)
    low_dose = models.TextField(db_column="low dose", blank=True, null=True)
    low_dose_mode = models.TextField(db_column="low dose mode", blank=True, null=True)
    objective_current = models.FloatField(db_column="objective current", blank=True, null=True)
    exp_wait_time = models.FloatField(db_column="exp wait time", blank=True, null=True)
    tem_energy_filtered = models.BooleanField(db_column="tem energy filtered", blank=True, null=True)
    tem_energy_filter = models.BooleanField(db_column="tem energy filter", blank=True, null=True)
    tem_energy_filter_width = models.FloatField(db_column="tem energy filter width", blank=True, null=True)
    probe_mode = models.TextField(db_column="probe mode", blank=True, null=True)
    class Meta:
        managed = False
        verbose_name = "ScopeEMData"
        verbose_name_plural = "ScopeEMData"
        db_table = "ScopeEMData"