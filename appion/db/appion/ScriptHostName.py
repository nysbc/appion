from django.db import models

class ScriptHostName(models.Model):
	def_id = models.AutoField(db_column="DEF_id", primary_key=True)
	def_timestamp = models.DateTimeField(
        db_column="DEF_timestamp", auto_now_add=True
    )

	name = models.TextField(blank=True,null=True)
	ip = models.TextField(blank=True,null=True)
	system = models.TextField(blank=True,null=True)
	distro = models.TextField(blank=True,null=True)
	arch = models.TextField(blank=True,null=True)
	nproc = models.IntegerField(blank=True,null=True)
	memory = models.IntegerField(blank=True,null=True)
	cpu_vendor = models.TextField(blank=True,null=True)
	gpu_vendor = models.TextField(blank=True,null=True)

	class Meta:
		managed = False
		verbose_name = "ScriptHostName"
		verbose_name_plural = "ScriptHostName"
		db_table = "ScriptHostName"