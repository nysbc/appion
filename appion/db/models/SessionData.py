from django.db import models
from .UserData import UserData

class SessionData(models.Model):
    def_id = models.AutoField(db_column="DEF_id", primary_key=True)
    def_timestamp = models.DateTimeField(
        db_column="DEF_timestamp", auto_now_add=True
    )
    name = models.TextField(blank=True, null=True)
    ref_userdata_user = models.ForeignKey(
        UserData,
        db_column="REF|UserData|user",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )
    image_path = models.TextField(db_column="image path", blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    hidden = models.IntegerField(blank=True, null=True)
    # ref_instrumentdata_instrument = models.IntegerField(
    #     db_column="REF|InstrumentData|instrument", blank=True, null=True
    # )
    ref_gridholderdata_holder = models.IntegerField(
        db_column="REF|GridHolderData|holder", blank=True, null=True
    )
    # frame_path = models.TextField(db_column="frame path", blank=True, null=True)

    def __str__(self):
        return self.name or "<no name>"

    class Meta:
        managed = False
        db_table = "SessionData"
        verbose_name = "SessionData"
        verbose_name_plural = "SessionData"