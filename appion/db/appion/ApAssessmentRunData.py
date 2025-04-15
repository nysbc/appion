from django.db import models
from ..models import SessionData

class ApAssessmentRunData(models.Model):
	def_id = models.AutoField(db_column="DEF_id", primary_key=True)
	def_timestamp = models.DateTimeField(
		db_column="DEF_timestamp", auto_now_add=True
	)
	ref_sessiondata_session = models.ForeignKey(
		SessionData,
		db_column="REF|SessionData|session",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	name = models.TextField(blank=True,null=True)
	class Meta:
		managed = False
		verbose_name = "ApAssessmentRunData"
		verbose_name_plural = "ApAssessmentRunData"
		db_table = "ApAssessmentRunData"