from django.db import models
from django.db.models import IntegerChoices
from django.utils import timezone

from user.models import User
from utils.common_utils import to_django_time


# Create your models here.

class ActivityType(IntegerChoices):
    """活动类型"""
    SPORTS = 0
    ART = 1
    SCIENCE = 2
    OTHER = 3


def default_sign_info():
    return dict(code="", valid_until=to_django_time(timezone.now()))


class Attender(models.Model):
    """活动签到"""
    activity = models.ForeignKey("Activity", on_delete=models.CASCADE, verbose_name="活动")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    sign_time = models.DateTimeField("签到时间", default=timezone.now)
    status = models.BooleanField("签到状态", default=False)

    def __str__(self):
        return f"ActivityAttender: {self.activity.name} {self.user.name}"

    class Meta:
        db_table = "activity_attendance"
        ordering = ("-id",)
        verbose_name = "活动签到记录"
        constraints = [
            models.UniqueConstraint(
                fields=("activity", "user"),
                name="unique_activity_attendance"
            )
        ]


class Activity(models.Model):
    """活动"""
    name = models.CharField("名称", max_length=50)
    description = models.TextField("描述", max_length=10240)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name="创建者", null=True)
    start_time = models.DateTimeField("开始时间")
    end_time = models.DateTimeField("结束时间")
    location = models.CharField("地点", max_length=50)
    capacity = models.PositiveIntegerField("最大报名容量")
    type = models.IntegerField("活动类别", choices=ActivityType.choices)
    # sign_code = models.CharField("签到码", max_length=50, null=True)
    # code_expired_time = models.DateTimeField("签到码过期时间", null=True)
    sign_info = models.JSONField("签到信息", default=default_sign_info)
    users = models.ManyToManyField(
        User, through=Attender, related_name="activity_attenders_set", verbose_name="参与者"
    )

    def __str__(self):
        return f"Activity: {self.name}"

    @property
    def is_started(self):
        return self.start_time < timezone.now()

    @property
    def is_running(self):
        return self.start_time < timezone.now() < self.end_time

    @property
    def is_end(self):
        return self.end_time < timezone.now()

    @property
    def get_attenders_count(self):
        return self.attender_set.count()

    @property
    def get_signed_attenders_count(self):
        return self.attender_set.filter(status=True).count()

    class Meta:
        db_table = "activity"
        ordering = ("-id",)
        verbose_name = "活动"
