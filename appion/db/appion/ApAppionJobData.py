from django.db import models
from .ApPathData import ApPathData
from ..models import SessionData

class ApAppionJobData(models.Model):
	def_id = models.AutoField(db_column="DEF_id", primary_key=True)
	def_timestamp = models.DateTimeField(
		db_column="DEF_timestamp", auto_now_add=True
	)
	ref_appathdata_path = models.ForeignKey(
		ApPathData,
		db_column="REF|ApPathData|path",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	ref_sessiondata_session = models.ForeignKey(
		SessionData,
		db_column="REF|SessionData|session",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	ref_appathdata_dmfpath = models.ForeignKey(
		ApPathData,
		db_column="REF|ApPathData|dmfpath",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	ref_appathdata_clusterpath= models.ForeignKey(
		ApPathData,
		db_column="REF|ApPathData|clusterpath",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	name = models.TextField(blank=True,null=True)
	cluster = models.TextField(blank=True,null=True)
	jobtype = models.TextField(blank=True,null=True)
	status = models.TextField(blank=True,null=True)
	user = models.TextField(blank=True,null=True)
	clusterjobid = models.IntegerField(blank=True,null=True)
	class Meta:
		managed = False
		verbose_name = "ApAppionJobData"
		verbose_name_plural = "ApAppionJobData"
		db_table = "ApAppionJobData"