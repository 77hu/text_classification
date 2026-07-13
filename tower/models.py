from django.db import models


class AttackRecord(models.Model):
    """持久化存储每一次攻击记录，用于预测引擎和数据分析。"""
    tower_id = models.CharField(max_length=2, verbose_name="城池ID")
    tower_name = models.CharField(max_length=20, verbose_name="城池名称")
    session_id = models.CharField(max_length=20, verbose_name="会话ID")
    left_time = models.IntegerField(default=0, verbose_name="剩余时间(秒)")
    attack_time = models.DateTimeField(verbose_name="攻击时间", db_index=True)
    predicted_cities = models.CharField(
        max_length=60, null=True, blank=True, verbose_name="预测城市",
        help_text="本轮攻击前预测的3个城市，逗号分隔",
    )
    prediction_correct = models.BooleanField(
        null=True, blank=True, verbose_name="预测是否正确",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        ordering = ["-attack_time"]
        verbose_name = "攻击记录"
        verbose_name_plural = "攻击记录"

    def __str__(self):
        return f"{self.tower_name} @ {self.attack_time}"
