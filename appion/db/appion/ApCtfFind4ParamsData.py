from django.db import models

class ApCtfFind4ParamsData(models.Model):
	def_id = models.AutoField(db_column="DEF_id", primary_key=True)
	def_timestamp = models.DateTimeField(
		db_column="DEF_timestamp", auto_now_add=True
	)
	bestdb = models.BooleanField(blank=True,null=True)
	ampcontrast = models.FloatField(blank=True,null=True)
	fieldsize = models.IntegerField(blank=True,null=True)
	cs = models.FloatField(blank=True,null=True)
	resmin = models.FloatField(blank=True,null=True)
	defstep = models.FloatField(blank=True,null=True)
	shift_phase = models.BooleanField(blank=True,null=True)
	min_phase_shift = models.FloatField(blank=True,null=True)
	max_phase_shift = models.FloatField(blank=True,null=True)
	phase_search_step = models.FloatField(blank=True,null=True)
	local_refine = models.BooleanField(blank=True,null=True)

	class Meta:
		managed = False
		verbose_name = "ApCtfFind4ParamsData"
		verbose_name_plural = "ApCtfFind4ParamsData"
		db_table = "ApCtfFind4ParamsData"