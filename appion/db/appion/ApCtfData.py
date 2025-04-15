

from django.db import models
from ..models import AcquisitionImageData
from .ApAceRunData import ApAceRunData

class ApCtfData(models.Model):
	def_id = models.AutoField(db_column="DEF_id", primary_key=True)
	def_timestamp = models.DateTimeField(
		db_column="DEF_timestamp", auto_now_add=True
	)
	ref_apacerundata_acerun = models.ForeignKey(
		ApAceRunData,
		db_column="REF|ApAceRunData|acerun",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	ref_acquisitionimagedata_image = models.ForeignKey(
		AcquisitionImageData,
		db_column="REF|AcquisitionImageData|image",
		blank=True,
		null=True,
		on_delete=models.DO_NOTHING,
	)
	# in millimeters
	cs = models.FloatField(blank=True,null=True)  
	# initial defocus
	defocusinit = models.FloatField(blank=True,null=True)  
	# sqrt(1-A^2)sin + A*cos format
	amplitude_contrast = models.FloatField(blank=True,null=True) 
	# in negative meters for underfocus |def1| < |def2|
	defocus1 = models.FloatField(blank=True,null=True)  
	# in negative meters for underfocus
	defocus2 = models.FloatField(blank=True,null=True)  
	# in counter-clockwise degrees from x-axis (degrees)
	angle_astigmatism = models.FloatField(blank=True,null=True) 
	# ctffind4 good fit resolution 
	ctffind4_resolution = models.FloatField(blank=True,null=True) 
	# classic confidence 
	confidence = models.FloatField(blank=True,null=True) 
	# classic confidence
	confidence_d = models.FloatField(blank=True,null=True) 
	# defined as confidence between 1/30 and 1/10 Angstroms 
	confidence_30_10 = models.FloatField(blank=True,null=True)  
	# defined as conidence of the first 5 peaks of the CTF
	confidence_5_peak = models.FloatField(blank=True,null=True)  
	# defined as confidence between 1/30 and 1/10 Angstroms
	overfocus_conf_30_10 = models.FloatField(blank=True,null=True)  
	# defined as conidence of the first 5 peaks of the CTF
	overfocus_conf_5_peak = models.FloatField(blank=True,null=True)  
	# resolution at 80% confidence
	resolution_80_percent = models.FloatField(blank=True,null=True) 
	# resolution at 50% confidence 
	resolution_50_percent = models.FloatField(blank=True,null=True)  
	# 2d powerspectra
	graph1 = models.TextField(blank=True,null=True) 
	# 1d plot showing fit 
	graph2 = models.TextField(blank=True,null=True) 
	# raw native powerspectra from software  
	graph3 = models.TextField(blank=True,null=True)  
	# raw native 1d plot from software 
	graph4 = models.TextField(blank=True,null=True) 
	# 2D plot for local CTF estimation 
	localplot = models.TextField(blank=True,null=True) 
	# local CTF output file
	localCTFstarfile = models.TextField(blank=True,null=True) 
	# used for ace2correct
	ctfvalues_file = models.TextField(blank=True,null=True) 
	# direct from ctffind/ctftilt 
	cross_correlation = models.FloatField(blank=True,null=True)  
	# from ctftilt
	tilt_angle = models.FloatField(blank=True,null=True) 
	# from ctftilt 
	tilt_axis_angle = models.FloatField(blank=True,null=True)  
	# from ACE1
	mat_file = models.TextField(blank=True,null=True)  
	#phase plate phase shift addition (radians)
	extra_phase_shift = models.FloatField(blank=True,null=True) 
	class Meta:
		managed = False
		verbose_name = "ApCtfData"
		verbose_name_plural = "ApCtfData"
		db_table = "ApCtfData"