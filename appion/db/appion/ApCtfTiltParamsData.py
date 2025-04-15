from django.db import models

class ApCtfTiltParamsData(models.Model):
	def_id = models.AutoField(db_column="DEF_id", primary_key=True)
	def_timestamp = models.DateTimeField(
		db_column="DEF_timestamp", auto_now_add=True
	)
	medium = models.TextField(blank=True,null=True)
	ampcarbon = models.FloatField(blank=True,null=True)
	ampice = models.FloatField(blank=True,null=True)
	fieldsize = models.IntegerField(blank=True,null=True)
	cs = models.FloatField(blank=True,null=True)
	bin = models.IntegerField(blank=True,null=True)
	resmin = models.FloatField(blank=True,null=True)
	resmax = models.FloatField(blank=True,null=True)
	defstep = models.FloatField(blank=True,null=True)
	dast = models.FloatField(blank=True,null=True)
	class Meta:
		managed = False
		verbose_name = "ApCtfTiltParamsData"
		verbose_name_plural = "ApCtfTiltParamsData"
		db_table = "ApCtfTiltParamsData"