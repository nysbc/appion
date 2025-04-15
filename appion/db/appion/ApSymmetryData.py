from django.db import models

class ApSymmetryData(models.Model):
	def_id = models.AutoField(db_column="DEF_id", primary_key=True)
	def_timestamp = models.DateTimeField(
		db_column="DEF_timestamp", auto_now_add=True
	)
	eman_name = models.TextField(blank=True,null=True)
	fold_symmetry = models.TextField(blank=True,null=True)
	symmetry = models.TextField(blank=True,null=True)
	description = models.TextField(blank=True,null=True)
	class Meta:
		managed = False
		verbose_name = "ApSymmetryData"
		verbose_name_plural = "ApSymmetryData"
		db_table = "ApSymmetryData"