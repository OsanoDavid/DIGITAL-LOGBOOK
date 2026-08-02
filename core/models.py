import os
import re
from datetime import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils.text import slugify
from .auth_utils import normalize_username

def _safe_upload_path(subdir, instance, filename):
    base_name, ext = os.path.splitext(filename)
    safe_name = slugify(base_name)[:50] or 'upload'
    username = slugify(getattr(instance.student, 'username', 'user'))[:30]
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{subdir}/{username}_{timestamp}_{safe_name}{ext}"


class User(AbstractUser):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('SUPERVISOR', 'Industry Supervisor'),
        ('LECTURER', 'University Lecturer'),
        ('ADMIN', 'System Administrator'),
        ('ATTACHMENT_ADMIN', 'Attachment Administrator'),
    )
    COURSE_PREFIX_MAP = {
        'IN13': 'Computer Science',
        'IN14': 'Applied Computer Science',
        'IN16': 'Software Engineering',
        'IN12': 'Information Technology',
    }

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    institution_or_company = models.CharField(max_length=255, blank=True, null=True, default="Kisii University (SIST)")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    course = models.CharField(max_length=120, blank=True, null=True)
    profile_photo = models.FileField(upload_to='profile_photos/', blank=True, null=True)
    
    # ADD THIS LINE HERE:
    avatar_color = models.CharField(max_length=7, default='0284c7')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('email'),
                name='unique_lower_email',
                condition=Q(email__isnull=False) & ~Q(email=''),
            )
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    # ... leave the rest of your models.py file exactly as it is
   
    @classmethod
    def infer_course_from_registration(cls, registration_number):
        if not registration_number:
            return None
        cleaned = re.sub(r'[^A-Za-z0-9]', '', registration_number).upper()
        for prefix, name in cls.COURSE_PREFIX_MAP.items():
            if cleaned.startswith(prefix):
                return name
        return None

    @classmethod
    def is_system_admin(cls, role_name):
        return role_name == 'ADMIN'

    @classmethod
    def is_attachment_admin(cls, role_name):
        return role_name == 'ATTACHMENT_ADMIN'

    @classmethod
    def is_admin_console_user(cls, role_name):
        return role_name in {'ADMIN', 'ATTACHMENT_ADMIN'}

    @classmethod
    def can_create_role(cls, actor_role, target_role):
        if cls.is_system_admin(actor_role):
            return True
        if cls.is_attachment_admin(actor_role):
            return target_role in {'STUDENT', 'SUPERVISOR', 'LECTURER', 'ATTACHMENT_ADMIN'}
        return False


class SystemSettings(models.Model):
    registration_enabled = models.BooleanField(default=True)
    registration_closed_message = models.CharField(max_length=255, default='Registration is temporarily closed by the system administrator.')

    class Meta:
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return 'System Settings'


class AttachmentPeriod(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE, related_name='attachment_profile')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_students')
    lecturer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_students')
    start_date = models.DateField()
    total_weeks = models.IntegerField(default=14, validators=[MinValueValidator(12), MaxValueValidator(16)])
    
    # Final Capstone Uploads & Grading Chain
    final_report = models.FileField(upload_to=lambda instance, filename: _safe_upload_path('sist_reports', instance, filename), max_length=255, blank=True, null=True)
    report_status = models.CharField(max_length=24, default='NOT_SUBMITTED')
    report_review_comment = models.TextField(blank=True, null=True)
    supervisor_marks = models.FloatField(null=True, blank=True)
    supervisor_comment = models.TextField(blank=True, null=True)
    supervisor_signed = models.BooleanField(default=False)
    
    lecturer_grade = models.CharField(max_length=2, blank=True, null=True)
    lecturer_marks = models.FloatField(null=True, blank=True)
    lecturer_comment = models.TextField(blank=True, null=True)
    lecturer_signed = models.BooleanField(default=False)

    # Academic Supervisor Visits
    first_visit_comment = models.TextField(blank=True, null=True)
    first_visit_date = models.DateField(blank=True, null=True)
    second_visit_comment = models.TextField(blank=True, null=True)
    second_visit_date = models.DateField(blank=True, null=True)

    # Student & Industry Supervisor final remarks (End of attachment)
    student_additional_info = models.TextField(blank=True, null=True)
    industry_supervisor_final_comment = models.TextField(blank=True, null=True)

    # Lecturer Document Upload for Grading
    week_7_grading_doc = models.FileField(upload_to=lambda instance, filename: _safe_upload_path('sist_reports/week7', instance, filename), max_length=255, blank=True, null=True)
    week_7_supervisor_marks = models.FloatField(null=True, blank=True)
    week_7_returned_doc = models.FileField(upload_to=lambda instance, filename: _safe_upload_path('sist_reports/week7_returned', instance, filename), max_length=255, blank=True, null=True)

    week_12_grading_doc = models.FileField(upload_to=lambda instance, filename: _safe_upload_path('sist_reports/week12', instance, filename), max_length=255, blank=True, null=True)
    week_12_supervisor_marks = models.FloatField(null=True, blank=True)
    week_12_returned_doc = models.FileField(upload_to=lambda instance, filename: _safe_upload_path('sist_reports/week12_returned', instance, filename), max_length=255, blank=True, null=True)

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

