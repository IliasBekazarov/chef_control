"""
Chef Control — API Models
"""
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ROLE_CHOICES = [("admin", "Admin"), ("user", "User")]
    user     = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role     = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    avatar   = models.ImageField(upload_to="avatars/", null=True, blank=True)
    location = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class DetectionSession(models.Model):
    """Бир иш күнүнүн / сессиянын жыйынтыгы"""
    session_id   = models.CharField(max_length=32, unique=True)
    started_at   = models.DateTimeField(auto_now_add=True)
    ended_at     = models.DateTimeField(null=True, blank=True)
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    total_checks = models.IntegerField(default=0)
    violations   = models.IntegerField(default=0)
    notes        = models.TextField(blank=True)

    @property
    def compliance_rate(self):
        if self.total_checks == 0:
            return 0.0
        return round((self.total_checks - self.violations) / self.total_checks * 100, 1)

    def __str__(self):
        return f"Session {self.session_id}"

    class Meta:
        ordering = ["-started_at"]


class DetectionRecord(models.Model):
    """Бир текшерүүнүн жыйынтыгы"""
    session       = models.ForeignKey(DetectionSession, on_delete=models.CASCADE,
                                      related_name="records", null=True, blank=True)
    timestamp     = models.DateTimeField()
    person_count  = models.IntegerField(default=0)
    # Hat
    has_hat       = models.BooleanField(default=False)
    hat_confidence= models.FloatField(default=0.0)
    # Apron
    has_apron     = models.BooleanField(default=False)
    apron_confidence = models.FloatField(default=0.0)
    # Result
    is_compliant  = models.BooleanField(default=False)
    violations    = models.TextField(blank=True)
    frame_image   = models.ImageField(upload_to="violations/", null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    def violations_list(self):
        return [v.strip() for v in self.violations.split("|") if v.strip()]

    def __str__(self):
        status = "✓" if self.is_compliant else "✗"
        return f"[{status}] {self.timestamp}"

    class Meta:
        ordering = ["-timestamp"]
