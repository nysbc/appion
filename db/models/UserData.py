from django.db import models

class UserData(models.Model):
    def_id = models.AutoField(db_column="DEF_id", primary_key=True)
    def_timestamp = models.DateTimeField(
        db_column="DEF_timestamp", auto_now_add=True
    )
    username = models.CharField(
        unique=True, max_length=24, blank=True, null=True
    )
    firstname = models.CharField(max_length=24, blank=True, null=True)
    lastname = models.CharField(max_length=24, blank=True, null=True)
    password = models.CharField(max_length=32, blank=True, null=True)
    email = models.CharField(max_length=60, blank=True, null=True)
    ref_groupdata_group = models.IntegerField(
        default=3, db_column="REF|GroupData|group", blank=False, null=False
    )
    noleginon = models.IntegerField(blank=True, null=True)
    advanced = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.username

    class Meta:
        managed = False
        db_table = "UserData"
        ordering = ("username",)
        verbose_name_plural = "UserData"
        verbose_name = "UserData"
