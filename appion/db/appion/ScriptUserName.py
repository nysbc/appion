


from django.db import models

class ScriptUserName(models.Model):
	def_id = models.AutoField(db_column="DEF_id", primary_key=True)
	def_timestamp = models.DateTimeField(
		db_column="DEF_timestamp", auto_now_add=True
	)
	name = models.TextField(blank=True,null=True)
	uid = models.IntegerField(blank=True,null=True)
	gid = models.IntegerField(blank=True,null=True)
	fullname = models.TextField(blank=True,null=True)
	class Meta:
		managed = False
		verbose_name = "ScriptUserName"
		verbose_name_plural = "ScriptUserName"
		db_table = "ScriptUserName"