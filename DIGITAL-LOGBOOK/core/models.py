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


def _sist_reports_upload_path(instance, filename):
    return _safe_upload_path('sist_reports', instance, filename)


def _sist_reports_week7_upload_path(instance, filename):
    return _safe_upload_path('sist_reports/week7', instance, filename)


def _sist_reports_week7_returned_upload_path(instance, filename):
    return _safe_upload_path('sist_reports/week7_returned', instance, filename)


def _sist_reports_week12_upload_path(instance, filename):
    return _safe_upload_path('sist_reports/week12', instance, filename)


def _sist_reports_week12_returned_upload_path(instance, filename):
    return _safe_upload_path('sist_reports/week12_returned', instance, filename)


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

    SCHOOL_CHOICES = (
        ('SIST', 'School of Information Sciences & Technology'),
        ('SASS', 'School of Arts and Social Sciences'),
        ('SOBE', 'School of Business and Economics'),
        ('SEDHURED', 'School of Education and Human Resource Development'),
        ('SHS', 'School of Health Sciences'),
        ('SLAW', 'School of Law'),
        ('SPAS', 'School of Pure and Applied Sciences'),
        ('SANRM', 'School of Agriculture and Natural Resources Management'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    school = models.CharField(max_length=20, choices=SCHOOL_CHOICES, blank=True, null=True)
    institution_or_company = models.CharField(max_length=255, blank=True, null=True, default="Kisii University (SIST)")
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    course = models.CharField(max_length=120, blank=True, null=True)
    profile_photo = models.FileField(upload_to='profile_photos/', blank=True, null=True)
    must_change_password = models.BooleanField(default=False)
    
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
    current_academic_year = models.CharField(max_length=20, default='2025/2026')
    term_start_date = models.DateField(blank=True, null=True)
    term_end_date = models.DateField(blank=True, null=True)
    submission_deadline_date = models.DateField(blank=True, null=True)
    logbook_lock_date = models.DateField(blank=True, null=True)
    default_new_account_role = models.CharField(max_length=30, default='STUDENT')
    require_password_reset = models.BooleanField(default=True)
    placement_approval = models.CharField(max_length=20, default='MANUAL')
    notification_frequency = models.CharField(max_length=20, default='WEEKLY')
    audit_retention = models.CharField(max_length=20, default='90 days')
    landing_last_year_completed = models.IntegerField(default=456)
    landing_total_last_5_years = models.IntegerField(default=1458)
    # Manual override for past years counts shown on the landing/admin dashboard.
    # Stored as a map: { '2025/2026': 4, '2024/2025': 0, ... }
    landing_manual_year_counts = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return 'System Settings'


class LecturerProfile(models.Model):
    """Professional information supplied when an administrator creates a lecturer."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lecturer_profile')
    workspace_role = models.CharField(max_length=120, blank=True)
    national_id = models.CharField(max_length=50, blank=True)
    specialization = models.CharField(max_length=120, blank=True)
    university = models.CharField(max_length=255, blank=True)
    faculty = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    university_email = models.EmailField(blank=True)

    def __str__(self):
        return f'Lecturer profile: {self.user}'


class AttachmentPeriod(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE, related_name='attachment_profile')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_students')
    lecturer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_students')
    field_supervisor_name = models.CharField(max_length=255, blank=True, null=True)
    field_supervisor_email = models.EmailField(blank=True, null=True)
    field_supervisor_phone = models.CharField(max_length=20, blank=True, null=True)
    field_supervisor_id = models.CharField(max_length=50, blank=True, null=True)
    field_supervisor_gender = models.CharField(max_length=20, blank=True, null=True)
    field_supervisor_organization = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    total_weeks = models.IntegerField(default=14, validators=[MinValueValidator(12), MaxValueValidator(16)])
    
    academic_year = models.CharField(max_length=20, default='2025/2026')
    is_archived = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='ACTIVE')
    
    # Final Capstone Uploads & Grading Chain
    final_report = models.FileField(upload_to=_sist_reports_upload_path, max_length=255, blank=True, null=True)
    recommendation_letter = models.FileField(upload_to=_sist_reports_upload_path, max_length=255, blank=True, null=True)
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
    week_7_grading_doc = models.FileField(upload_to=_sist_reports_week7_upload_path, max_length=255, blank=True, null=True)
    week_7_supervisor_marks = models.FloatField(null=True, blank=True)
    week_7_returned_doc = models.FileField(upload_to=_sist_reports_week7_returned_upload_path, max_length=255, blank=True, null=True)

    week_12_grading_doc = models.FileField(upload_to=_sist_reports_week12_upload_path, max_length=255, blank=True, null=True)
    week_12_supervisor_marks = models.FloatField(null=True, blank=True)
    week_12_returned_doc = models.FileField(upload_to=_sist_reports_week12_returned_upload_path, max_length=255, blank=True, null=True)


class AdminNotification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_notifications')
    message = models.TextField()
    related_period = models.ForeignKey(AttachmentPeriod, on_delete=models.CASCADE, null=True, blank=True)
    action_url = models.CharField(max_length=512, blank=True, null=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification to {self.recipient.get_full_name() or self.recipient.username}: {self.message[:50]}"

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

