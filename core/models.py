import re
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from .auth_utils import normalize_username

class User(AbstractUser):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('SUPERVISOR', 'Industry Supervisor'),
        ('LECTURER', 'University Lecturer'),
    )
    COURSE_PREFIX_MAP = {
        'IN13': 'Computer Science',
        'IN14': 'Applied Computer Science',
        'IN16': 'Software Engineering',
        'IN12': 'Information Technology',
    }

    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='STUDENT')
    institution_or_company = models.CharField(max_length=255, blank=True, null=True, default="Kisii University (SIST)")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    course = models.CharField(max_length=120, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @classmethod
    def infer_course_from_registration(cls, registration_number):
        if not registration_number:
            return None
        cleaned = re.sub(r'[^A-Za-z0-9]', '', registration_number).upper()
        for prefix, name in cls.COURSE_PREFIX_MAP.items():
            if cleaned.startswith(prefix):
                return name
        return None

class AttachmentPeriod(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE, related_name='attachment_profile')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_students')
    lecturer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_students')
    start_date = models.DateField()
    total_weeks = models.IntegerField(default=14, validators=[MinValueValidator(12), MaxValueValidator(16)])
    
    # Final Capstone Uploads & Grading Chain
    final_report = models.FileField(upload_to='sist_reports/', blank=True, null=True)
    supervisor_marks = models.FloatField(null=True, blank=True)
    supervisor_comment = models.TextField(blank=True, null=True)
    supervisor_signed = models.BooleanField(default=False)
    
    lecturer_grade = models.CharField(max_length=2, blank=True, null=True)
    lecturer_marks = models.FloatField(null=True, blank=True)
    lecturer_comment = models.TextField(blank=True, null=True)
    lecturer_signed = models.BooleanField(default=False)

    def __str__(self):
        return f"SIST Logbook Profile - {self.student.username}"

class WeeklyLog(models.Model):
    profile = models.ForeignKey(AttachmentPeriod, on_delete=models.CASCADE, related_name='weekly_logs')
    week_number = models.PositiveIntegerField()
    
    monday_activity = models.TextField(blank=True, null=True)
    tuesday_activity = models.TextField(blank=True, null=True)
    wednesday_activity = models.TextField(blank=True, null=True)
    thursday_activity = models.TextField(blank=True, null=True)
    friday_activity = models.TextField(blank=True, null=True)
    
    supervisor_approved = models.BooleanField(default=False)
    supervisor_comment = models.TextField(blank=True, null=True)
    
    lecturer_approved = models.BooleanField(default=False)
    lecturer_comment = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('profile', 'week_number')
        ordering = ['week_number']