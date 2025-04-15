from django.db import models
from .ScriptProgramName import ScriptProgramName
from .ScriptUserName import ScriptUserName
from .ScriptHostName import ScriptHostName
from .ApPathData import ApPathData
from .ApAppionJobData import ApAppionJobData

class ScriptProgramRun(models.Model):
	def_id = models.AutoField(db_column="DEF_id", primary_key=True)
	def_timestamp = models.DateTimeField(
		db_column="DEF_timestamp", auto_now_add=True
	)
	runname = models.TextField(blank=True,null=True)
	revision = models.TextField(blank=True,null=True)
	ref_scriptprogramname_progname = models.ForeignKey(
		ScriptProgramName,
		db_column="REF|ScriptProgramName|progname",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	ref_scriptusername_username = models.ForeignKey(
		ScriptUserName,
		db_column="REF|ScriptUserName|username",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	ref_scripthostname_hostname = models.ForeignKey(
		ScriptHostName,
		db_column="REF|ScriptHostName|hostname",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	ref_appathdata_rundir = models.ForeignKey(
		ApPathData,
		db_column="REF|ApPathData|rundir",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	ref_apappionjobdata_job= models.ForeignKey(
		ApAppionJobData,
		db_column="REF|ApAppionJobData|job",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	ref_appathdata_appion_path = models.ForeignKey(
		ApPathData,
		db_column="REF|ApPathData|appion_path",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	unixshell = models.TextField(blank=True,null=True)
	class Meta:
		managed = False
		verbose_name = "ScriptProgramRun"
		verbose_name_plural = "ScriptProgramRun"
		db_table = "ScriptProgramRun"