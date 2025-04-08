from django.db import models

class InstrumentData(models.Model):
    def_id = models.AutoField(db_column="DEF_id", primary_key=True)
    def_timestamp = models.DateTimeField(
        db_column="DEF_timestamp", auto_now_add=True
    )
    name = models.TextField(blank=True, null=True)
    hostname = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    cs = models.FloatField(blank=True, null=True)
    pixelmax = models.IntegerField(blank=True, null=True)
    hidden = models.BooleanField(blank=True, null=True)
    class Meta:
        managed = False
        verbose_name = "InstrumentData"
        verbose_name_plural = "InstrumentData"
        db_table = "InstrumentData"
