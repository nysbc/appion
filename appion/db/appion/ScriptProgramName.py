from django.db import models

class ScriptProgramName(models.Model):
    def_id = models.AutoField(db_column="DEF_id", primary_key=True)
    def_timestamp = models.DateTimeField(
        db_column="DEF_timestamp", auto_now_add=True
    )
    name = models.TextField(blank=True,null=True)
    class Meta:
        managed = False
        verbose_name = "ScriptProgramName"
        verbose_name_plural = "ScriptProgramName"
        db_table = "ScriptProgramName"