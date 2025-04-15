from django.db import models
from .ScriptProgramName import ScriptProgramName

class ScriptParamName(models.Model):
	def_id = models.AutoField(db_column="DEF_id", primary_key=True)
	def_timestamp = models.DateTimeField(
		db_column="DEF_timestamp", auto_now_add=True
	)
	name = models.TextField(blank=True,null=True)
	ref_scriptprogramname_progname = models.ForeignKey(
		ScriptProgramName,
		db_column="REF|ScriptProgramName|progname",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	class Meta:
		managed = False
		verbose_name = "ScriptParamName"
		verbose_name_plural = "ScriptParamName"
		db_table = "ScriptParamName"