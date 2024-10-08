from django.db import models


# Create your models here.

class Grade(models.Model):
    """年级"""
    name = models.CharField("年级", max_length=50, unique=True)

    def __str__(self):
        return f"Grade: {self.name}"

    class Meta:
        db_table = "grade"
        ordering = ("-id",)
        verbose_name = "年级"


class Group(models.Model):
    """班级"""
    name = models.CharField("班级", max_length=50, unique=True)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)

    def __str__(self):
        return f"Group: {self.name}"

    class Meta:
        db_table = "group"
        ordering = ("-id",)
        verbose_name = "班级"
