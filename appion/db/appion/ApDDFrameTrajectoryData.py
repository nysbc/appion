from django.db import models
from ..models import AcquisitionImageData
from ApDDStackRunData import ApDDStackRunData

class ApDDFrameTrajectoryData(models.Model):
    '''
    Retake of ApFrameAlignTrajectory. Save typically 10 frames
    plus the last frame which is just enough to view the
    trend to save space.
    '''
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
    # Technically a foreign key, but the table it refers to is never
    # populated and the entire column is filled with NULLs.
    ref_apstackparticledata_particle = models.IntegerField(
        db_column="REF|ApStackParticleData|particle",
        blank=True,
        null=True
    )
    ref_apddstackrundata_ddstackrun = models.ForeignKey(
        ApDDStackRunData,
        db_column="REF|ApDDStackRunData|ddstackrun",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    #pixels relative to reference frame of the first 10 frames
    seq_pos_x = models.TextField(db_column="SEQ|pos_x", blank=True, null=True)
    #pixels relative to reference frame of the first 10 frames
    seq_pos_y = models.TextField(db_column="SEQ|pos_y", blank=True, null=True)
    #pixels relative to reference frame
    last_x = models.FloatField(blank=True,null=True)
    #pixels relative to reference frame
    last_y = models.FloatField(blank=True,null=True)
    #number of frames in the alignment
    number_of_positions = models.IntegerField(blank=True,null=True) 
    #reference frame index, base=0
    reference_index = models.IntegerField(blank=True,null=True)
    class Meta:
        managed = False
        verbose_name = "ApDDFrameTrajectoryData"
        verbose_name_plural = "ApDDFrameTrajectoryData"
        db_table = "ApDDFrameTrajectoryData"