


from django.db import models
from ..models import SessionData
from ApCtfTiltParamsData import ApCtfTiltParamsData
from ApCtfFind4ParamsData import ApCtfFind4ParamsData
from ApPathData import ApPathData

class ApAceRunData(models.Model):
	def_id = models.AutoField(db_column="DEF_id", primary_key=True)
	def_timestamp = models.DateTimeField(
		db_column="DEF_timestamp", auto_now_add=True
	)

	# ApAceParamsData is unused so no foreign key here.
	ref_apaceparamsdata_aceparams = models.IntegerField(
		db_column="REF|ApAceParamsData|aceparams",
		blank=True,
		null=True
	)
	ref_apctftiltparamsdata_ctftilt_params = models.ForeignKey(
		ApCtfTiltParamsData,
		db_column="REF|ApCtfTiltParamsData|ctftilt_params",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	# ApXmippCtfParamsData is unused so no foreign key here.
	ref_apxmippctfparamsdata_xmipp_ctf_params = models.IntegerField(
		db_column="REF|ApXmippCtfParamsData|xmipp_ctf_params",
		blank=True,
		null=True
	)
	# ApAce2ParamsData is unused so no foreign key here.
	ref_apace2paramsdata_ace2_params = models.IntegerField(
		db_column="REF|ApAce2ParamsData|ace2_params",
		blank=True,
		null=True
	)
	ref_apctffind4paramsdata_ctffind4_params = models.ForeignKey(
		ApCtfFind4ParamsData,
		db_column="REF|ApCtfFind4ParamsData|ctffind4_params",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	transferred = models.BooleanField(blank=True,null=True)
	# ApAceTransferParamsData is unused so no foreign key here.
	ref_apacetransferparamsdat_transfer_params = models.IntegerField(
		db_column="REF|ApAceTransferParamsData|transfer_params",
		blank=True,
		null=True
	)
	ref_sessiondata_session = models.ForeignKey(
		SessionData,
		db_column="REF|SessionData|session",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	ref_appathdata_path = models.ForeignKey(
		ApPathData,
		db_column="REF|ApPathData|path",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	name = models.TextField(blank=True,null=True)
	hidden = models.BooleanField(blank=True,null=True)

	class Meta:
		managed = False
		verbose_name = "ApAceRunData"
		verbose_name_plural = "ApAceRunData"
		db_table = "ApAceRunData"