from django.db import models

# Create your models here.

class Files(models.Model):
    file_id = models.CharField(max_length=1000)
    upload_time = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"file: {self.id}"

    class Meta:
        ordering = ("-id",)
        db_table = "Files"  # 数据库表名
        verbose_name = "文件"