import os

APP_NAME = "core"

files_to_create = {
    # 1. ADVANCED MULTI-ROLE MODELS & LOCK ENGINE
    f"{APP_NAME}/models.py": '''from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    ROLE_CHOICES = (
        ('STUDENT', 'Student'),
        ('SUPERVISOR', 'Industry Supervisor'),
        ('LECTURER', 'University Lecturer'),
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='STUDENT')
    institution_or_company = models.CharField(max_length=255, blank=True, null=True, default="Kisii University (SIST)")
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

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
''',

    # 2. COMPLETE EVALUATION AND CAPSTONE FORMS
    f"{APP_NAME}/forms.py": '''from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, WeeklyLog, AttachmentPeriod

class SISTRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'role', 'phone_number')

class SISTLoginForm(AuthenticationForm):
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial='STUDENT')

class LogEntryForm(forms.ModelForm):
    class Meta:
        model = WeeklyLog
        fields = ['monday_activity', 'tuesday_activity', 'wednesday_activity', 'thursday_activity', 'friday_activity']
        widgets = {day: forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}) for day in ['monday_activity', 'tuesday_activity', 'wednesday_activity', 'thursday_activity', 'friday_activity']}

class SupervisorCommentForm(forms.ModelForm):
    class Meta:
        model = WeeklyLog
        fields = ['supervisor_comment', 'supervisor_approved']

class LecturerSignForm(forms.ModelForm):
    class Meta:
        model = WeeklyLog
        fields = ['lecturer_comment', 'lecturer_approved']

class FinalReportForm(forms.ModelForm):
    class Meta:
        model = AttachmentPeriod
        fields = ['final_report']

class FinalSupervisorGradingForm(forms.ModelForm):
    class Meta:
        model = AttachmentPeriod
        fields = ['supervisor_marks', 'supervisor_comment', 'supervisor_signed']

class FinalLecturerGradingForm(forms.ModelForm):
    class Meta:
        model = AttachmentPeriod
        fields = ['lecturer_marks', 'lecturer_grade', 'lecturer_comment', 'lecturer_signed']
''',

    # 3. FULL DATA PIPELINE VIEWS
    f"{APP_NAME}/views.py": '''from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import User, AttachmentPeriod, WeeklyLog
from .forms import SISTRegistrationForm, SISTLoginForm, LogEntryForm, SupervisorCommentForm, LecturerSignForm, FinalReportForm, FinalSupervisorGradingForm, FinalLecturerGradingForm

def login_view(request):
    if request.method == 'POST':
        form = SISTLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.role != request.POST.get('role'):
                form.add_error(None, "Selected portal access role mismatch.")
            else:
                login(request, user)
                return redirect('dashboard')
    else:
        form = SISTLoginForm()
    return render(request, 'core/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = SISTRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SISTRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    user = request.user
    if user.role == 'STUDENT':
        period, _ = AttachmentPeriod.objects.get_or_create(student=user, defaults={'start_date': '2026-01-01'})
        for w in range(1, period.total_weeks + 1):
            WeeklyLog.objects.get_or_create(profile=period, week_number=w)
        
        report_form = FinalReportForm(instance=period)
        if request.method == 'POST' and 'upload_report' in request.POST:
            report_form = FinalReportForm(request.POST, request.FILES, instance=period)
            if report_form.is_valid():
                report_form.save()
                return redirect('dashboard')

        return render(request, 'core/student_dashboard.html', {'period': period, 'logs': period.weekly_logs.all(), 'report_form': report_form})
        
    elif user.role == 'SUPERVISOR':
        students = AttachmentPeriod.objects.filter(supervisor=user)
        return render(request, 'core/supervisor_dashboard.html', {'students': students})
        
    elif user.role == 'LECTURER':
        students = AttachmentPeriod.objects.filter(lecturer=user)
        return render(request, 'core/lecturer_dashboard.html', {'students': students})

@login_required
def edit_week_log(request, log_id):
    log = get_object_or_404(WeeklyLog, id=log_id, profile__student=request.user)
    if log.supervisor_approved:
        return HttpResponseForbidden("This week's entry has been verified and locked.")
    if request.method == 'POST':
        form = LogEntryForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = LogEntryForm(instance=log)
    return render(request, 'core/edit_log.html', {'form': form, 'log': log})

@login_required
def supervisor_review_log(request, log_id):
    if request.user.role != 'SUPERVISOR': return HttpResponseForbidden()
    log = get_object_or_404(WeeklyLog, id=log_id, profile__supervisor=request.user)
    if request.method == 'POST':
        form = SupervisorCommentForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = SupervisorCommentForm(instance=log)
    return render(request, 'core/review_log.html', {'form': form, 'log': log, 'role': 'Supervisor'})

@login_required
def lecturer_sign_log(request, log_id):
    if request.user.role != 'LECTURER': return HttpResponseForbidden()
    log = get_object_or_404(WeeklyLog, id=log_id, profile__lecturer=request.user)
    if not log.supervisor_approved:
        return HttpResponseForbidden("You can only sign logs that have been verified by the Industry Supervisor.")
    if request.method == 'POST':
        form = LecturerSignForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = LecturerSignForm(instance=log)
    return render(request, 'core/review_log.html', {'form': form, 'log': log, 'role': 'Lecturer'})

@login_required
def final_grading_view(request, period_id):
    period = get_object_or_404(AttachmentPeriod, id=period_id)
    if request.user.role == 'SUPERVISOR' and period.supervisor == request.user:
        form = FinalSupervisorGradingForm(instance=period)
        if request.method == 'POST':
            form = FinalSupervisorGradingForm(request.POST, instance=period)
            if form.is_valid(): form.save(); return redirect('dashboard')
        return render(request, 'core/final_grading.html', {'form': form, 'period': period, 'role': 'Supervisor'})
        
    elif request.user.role == 'LECTURER' and period.lecturer == request.user:
        if not period.supervisor_signed:
            return HttpResponseForbidden("Waiting for Industry Supervisor's final assessment and signature.")
        form = FinalLecturerGradingForm(instance=period)
        if request.method == 'POST':
            form = FinalLecturerGradingForm(request.POST, instance=period)
            if form.is_valid(): form.save(); return redirect('dashboard')
        return render(request, 'core/final_grading.html', {'form': form, 'period': period, 'role': 'Lecturer'})
    return HttpResponseForbidden()
''',

    # 4. URL ROUTING EXCHANGER
    f"{APP_NAME}/urls.py": '''from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('log/edit/<int:log_id>/', views.edit_week_log, name='edit_log'),
    path('log/review/supervisor/<int:log_id>/', views.supervisor_review_log, name='supervisor_review'),
    path('log/sign/lecturer/<int:log_id>/', views.lecturer_sign_log, name='lecturer_sign'),
    path('grading/final/<int:period_id>/', views.final_grading_view, name='final_grading'),
]
''',

    # 5. PREMIUM PROFESSIONAL KISII UNIVERSITY STYLE ARCHITECTURE CSS
    f"static/css/sist_style.css": '''
:root { --kisii-blue: #0f4c81; --sist-gold: #f4a261; --slate: #1e293b; --light-slate: #f8fafc; --border: #cbd5e1; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--light-slate); color: var(--slate); margin:0; padding:0; }
header { background: #ffffff; border-bottom: 4px solid var(--kisii-blue); padding: 15px 5%; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
.header-brand h1 { margin:0; font-size:22px; color: var(--kisii-blue); font-weight:800; }
.header-brand p { margin:0; font-size:12px; color: var(--sist-gold); font-weight:700; text-transform: uppercase; }
.main-container { max-width: 1200px; margin: 40px auto; padding: 0 20px; }
.card { background: #ffffff; border-radius: 12px; border: 1px solid var(--border); padding: 30px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.04); margin-bottom: 30px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; background:#fff; border-radius: 8px; overflow:hidden; }
th, td { padding: 14px 18px; border-bottom: 1px solid var(--border); text-align: left; }
th { background: var(--kisii-blue); color: white; font-weight: 600; }
tr:hover { background-color: #f1f5f9; }
.btn { padding: 10px 20px; border-radius: 6px; font-weight:600; text-decoration:none; display:inline-block; border:none; cursor:pointer; font-size:14px; }
.btn-blue { background: var(--kisii-blue); color: white; }
.btn-gold { background: var(--sist-gold); color: white; }
.btn-danger { background: #ef4444; color: white; }
.badge { padding: 6px 12px; border-radius: 50px; font-size: 12px; font-weight:700; }
.badge-success { background: #d1fae5; color: #065f46; }
.badge-warning { background: #fef3c7; color: #92400e; }
.form-input { width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border); background:#fff; box-sizing: border-box; }
''',

    # 6. SIGN IN INTERFACE UI (Matching image_e48c44.jpg)
    f"templates/core/login.html": '''<!DOCTYPE html>
<html>
<head>
    <title>SIST Portal - Sign In</title>
    <link rel="stylesheet" href="/static/css/sist_style.css">
    <style>
        .split-box { display: flex; min-height: 500px; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }
        .hero-section { flex: 1.2; background: linear-gradient(135deg, #0f4c81 0%, #1e3a8a 100%); color: white; padding: 50px; display: flex; flex-direction: column; justify-content: center; }
        .form-section { flex: 0.8; background: white; padding: 50px; display: flex; flex-direction: column; justify-content: center; }
    </style>
</head>
<body>
    <header>
        <div class="header-brand"><h1>KISII UNIVERSITY</h1><p>School of Information Sciences & Technology</p></div>
    </header>
    <div class="main-container" style="max-width: 950px; margin-top: 60px;">
        <div class="split-box">
            <div class="hero-section">
                <h1 style="font-size:38px; margin-bottom:15px;">SIST Digital Attachment Logbook</h1>
                <p style="font-size:15px; line-height:1.6; opacity:0.9;">A centralized portal platform for Kisii University students, industry coordinators, and academic supervisors to seamlessly manage, verify, and track attachment milestones.</p>
            </div>
            <div class="form-section">
                <h2 style="color: var(--kisii-blue); margin-top:0;">Sign In to Portal</h2>
                <form method="POST">
                    {% csrf_token %}
                    <p><label>Select Portal View Mode:</label><br>{{ form.role }}</p>
                    <p><label>Username:</label><br><input type="text" name="username" class="form-input" required></p>
                    <p><label>Password:</label><br><input type="password" name="password" class="form-input" required></p>
                    {% if form.errors %}<p style="color:red; font-size:13px;">Invalid configuration profile alignment credentials.</p>{% endif %}
                    <button type="submit" class="btn btn-gold" style="width:100%; margin-top:10px;">Sign In to Portal</button>
                </form>
                <p style="text-align:center; margin-top:20px; font-size:14px;">New Student? <a href="{% url 'register' %}" style="color:var(--kisii-blue); font-weight:700;">Create Account</a></p>
            </div>
        </div>
    </div>
</body>
</html>
''',

    # 7. REGISTRATION TEMPLATE
    f"templates/core/register.html": '''<!DOCTYPE html>
<html>
<head>
    <title>SIST Portal - Register</title>
    <link rel="stylesheet" href="/static/css/sist_style.css">
</head>
<body>
    <div class="main-container" style="max-width: 500px; margin-top: 60px;">
        <div class="card">
            <h2 style="color:var(--kisii-blue); margin-top:0;">SIST System Registration</h2>
            <form method="POST">
                {% csrf_token %}
                {% for field in form %}
                    <p><label>{{ field.label }}</label><br>{{ field }}</p>
                {% endfor %}
                <button type="submit" class="btn btn-blue" style="width:100%;">Create Account</button>
            </form>
        </div>
    </div>
</body>
</html>
''',

    # 8. COMPLETE STUDENT LOGBOOK MANAGEMENT AND REPORT UPLOADER HUB
    f"templates/core/student_dashboard.html": '''<!DOCTYPE html>
<html>
<head>
    <title>SIST Logbook - Student Workspace</title>
    <link rel="stylesheet" href="/static/css/sist_style.css">
</head>
<body>
    <header>
        <div class="header-brand"><h1>SIST DIGITAL LOGBOOK</h1><p>Student Portal Workspace</p></div>
        <a href="{% url 'logout' %}" class="btn btn-danger">Logout</a>
    </header>
    <div class="main-container">
        <div class="grid-2">
            <div class="card">
                <h3>Attachment Details</h3>
                <p><strong>Field Supervisor:</strong> {{ period.supervisor.get_full_name|default:"Awaiting Field Allocation" }}</p>
                <p><strong>KU Lecturer:</strong> {{ period.lecturer.get_full_name|default:"Awaiting Departmental Assignment" }}</p>
            </div>
            <div class="card">
                <h3>Final grading Results</h3>
                {% if period.lecturer_signed %}
                    <p style="font-size:22px;">Final Grade: <strong style="color:var(--kisii-blue);">{{ period.lecturer_grade }}</strong> ({{ period.lecturer_marks }}%)</p>
                    <p><em>Lecturer Comment: {{ period.lecturer_comment }}</em></p>
                {% else %}
                    <p style="color:#b45309; font-weight:700;">Final verification evaluations ongoing.</p>
                {% endif %}
            </div>
        </div>

        <!-- CAPSTONE 14-WEEK REPORT UPLOADER -->
        <div class="card">
            <h3>Final Assessment Report Submission Hub (Minimum 12-14 Weeks Completed)</h3>
            {% if not period.supervisor_signed %}
                <form method="POST" enctype="multipart/form-data">
                    {% csrf_token %}
                    {{ report_form.as_p }}
                    <button type="submit" name="upload_report" class="btn btn-blue">Upload Report Document</button>
                </form>
            {% else %}
                <p style="color:green; font-weight:700;">✓ Final documents locked and compiled for grade allocation.</p>
                {% if period.final_report %}<a href="{{ period.final_report.url }}" class="btn btn-blue" download>Download Submitted File</a>{% endif %}
            {% endif %}
        </div>

        <div class="card">
            <h3>Weekly Logs Pipeline Matrices</h3>
            <table>
                <thead>
                    <tr><th>Week</th><th>Status</th><th>Supervisor Remarks</th><th>Lecturer Signature</th><th>Action</th></tr>
                </thead>
                <tbody>
                    {% for log in logs %}
                    <tr>
                        <td><strong>Week {{ log.week_number }}</strong></td>
                        <td>
                            {% if log.supervisor_approved %}
                                <span class="badge badge-success">Approved & Locked</span>
                            {% else %}
                                <span class="badge badge-warning">Draft Mode</span>
                            {% endif %}
                        </td>
                        <td>{{ log.supervisor_comment|default:"No evaluations added" }}</td>
                        <td>{{ log.lecturer_comment|default:"No academic signature" }}</td>
                        <td>
                            {% if not log.supervisor_approved %}
                                <a href="{% url 'edit_log' log.id %}" class="btn btn-gold" style="padding:5px 12px;">Fill Days</a>
                            {% else %}
                                <button class="btn btn-blue" style="padding:5px 12px; background:#64748b;" onclick="window.print()">Download/Print</button>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
''',

    # 9. INDUSTRY FIELD SUPERVISOR DASHBOARD
    f"templates/core/supervisor_dashboard.html": '''<!DOCTYPE html>
<html>
<head>
    <title>SIST Logbook - Industry Supervisor</title>
    <link rel="stylesheet" href="/static/css/sist_style.css">
</head>
<body>
    <header>
        <div class="header-brand"><h1>KISII UNIVERSITY SIST</h1><p>Industry Supervisor Workspace</p></div>
        <a href="{% url 'logout' %}" class="btn btn-danger">Logout</a>
    </header>
    <div class="main-container">
        <div class="card">
            <h2>Allocated Student Attachés</h2>
            <table>
                <thead>
                    <tr><th>Student Name</th><th>Company / Station</th><th>Weekly Records Check</th><th>Capstone Assessment</th></tr>
                </thead>
                <tbody>
                    {% for p in students %}
                    <tr>
                        <td><strong>{{ p.student.get_full_name }}</strong></td>
                        <td>{{ p.student.institution_or_company }}</td>
                        <td>
                            {% for log in p.weekly_logs.all %}
                                <a href="{% url 'supervisor_review' log.id %}" style="margin-right:5px; text-decoration:none; color:{% if log.supervisor_approved %}green{% else %}#b45309{% endif %};">W{{ log.week_number }}</a>
                            {% endfor %}
                        </td>
                        <td>
                            {% if p.final_report %}
                                <a href="{% url 'final_grading' p.id %}" class="btn btn-gold" style="padding:4px 10px;">Grade Student</a>
                            {% else %}
                                <span style="font-size:12px; color:gray;">Report pending upload</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
''',

    # 10. ACADEMIC LECTURER DASHBOARD (Shows only Supervisor-approved metrics)
    f"templates/core/lecturer_dashboard.html": '''<!DOCTYPE html>
<html>
<head>
    <title>SIST Logbook - Lecturer Dashboard</title>
    <link rel="stylesheet" href="/static/css/sist_style.css">
</head>
<body>
    <header>
        <div class="header-brand"><h1>KISII UNIVERSITY SIST</h1><p>Lecturer Sign-off Space</p></div>
        <a href="{% url 'logout' %}" class="btn btn-danger">Logout</a>
    </header>
    <div class="main-container">
        <div class="card">
            <h2>Assigned Student Cohort</h2>
            <table>
                <thead>
                    <tr><th>Attachee Student</th><th>Company Verification Status</th><th>Weekly Sign-Offs</th><th>Final Academic Grade</th></tr>
                </thead>
                <tbody>
                    {% for p in students %}
                    <tr>
                        <td><strong>{{ p.student.get_full_name }}</strong></td>
                        <td>{% if p.supervisor_signed %}<span style="color:green; font-weight:700;">Company Verified</span>{% else %}<span style="color:gray;">Field Assessment Pending</span>{% endif %}</td>
                        <td>
                            {% for log in p.weekly_logs.all %}
                                {% if log.supervisor_approved %}
                                    <a href="{% url 'lecturer_sign' log.id %}" style="margin-right:5px; text-decoration:none; color:{% if log.lecturer_approved %}blue{% else %}red{% endif %};">W{{ log.week_number }}</a>
                                {% endif %}
                            {% endfor %}
                        </td>
                        <td>
                            {% if p.supervisor_signed %}
                                <a href="{% url 'final_grading' p.id %}" class="btn btn-blue" style="padding:4px 10px;">Allocate Final Grade</a>
                            {% else %}
                                <span style="font-size:12px; color:gray;">Locked</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
''',

    # 11. DAY-BY-DAY LOG ENTRY FORM FOR STUDENTS
    f"templates/core/edit_log.html": '''<!DOCTYPE html>
<html>
<head>
    <title>Fill Logbook - SIST</title>
    <link rel="stylesheet" href="/static/css/sist_style.css">
</head>
<body>
    <div class="main-container" style="max-width: 750px;">
        <div class="card">
            <h2 style="color:var(--kisii-blue); margin-top:0;">Record Logbook Activities: Week {{ log.week_number }}</h2>
            <form method="POST">
                {% csrf_token %}
                {% for field in form %}<p><label style="font-weight:700; color:var(--kisii-blue);">{{ field.label }}</label><br>{{ field }}</p>{% endfor %}
                <button type="submit" class="btn btn-blue">Save Log Entry</button>
                <a href="{% url 'dashboard' %}" class="btn btn-gold" style="background:gray;">Back</a>
            </form>
        </div>
    </div>
</body>
</html>
''',

    # 12. REVIEW LOG DATA FORM FOR STAFF MEMBERS
    f"templates/core/review_log.html": '''<!DOCTYPE html>
<html>
<head>
    <title>Review Log - {{ role }}</title>
    <link rel="stylesheet" href="/static/css/sist_style.css">
</head>
<body>
    <div class="main-container" style="max-width: 700px;">
        <div class="card">
            <h2>{{ role }} Verification Workspace - Week {{ log.week_number }}</h2>
            <div style="background:#f1f5f9; padding:15px; border-radius:6px; margin-bottom:20px;">
                <p><strong>Monday:</strong> {{ log.monday_activity|default:"-" }}</p>
                <p><strong>Tuesday:</strong> {{ log.tuesday_activity|default:"-" }}</p>
                <p><strong>Wednesday:</strong> {{ log.wednesday_activity|default:"-" }}</p>
                <p><strong>Thursday:</strong> {{ log.thursday_activity|default:"-" }}</p>
                <p><strong>Friday:</strong> {{ log.friday_activity|default:"-" }}</p>
            </div>
            <form method="POST">
                {% csrf_token %}
                {{ form.as_p }}
                <button type="submit" class="btn btn-blue">Save Evaluation Sign-Off</button>
            </form>
        </div>
    </div>
</body>
</html>
''',

    # 13. RECTO-VERSO FINAL EVALUATION FORM
    f"templates/core/final_grading.html": '''<!DOCTYPE html>
<html>
<head>
    <title>Final Grading - {{ role }}</title>
    <link rel="stylesheet" href="/static/css/sist_style.css">
</head>
<body>
    <div class="main-container" style="max-width:650px;">
        <div class="card">
            <h2>Final Capstone Grading Panel - {{ role }} View</h2>
            <p><strong>Student:</strong> {{ period.student.get_full_name }}</p>
            {% if period.final_report %}<p>📥 <a href="{{ period.final_report.url }}" download>Download Submitted Report Document File</a></p>{% endif %}
            <hr>
            <form method="POST">
                {% csrf_token %}
                {{ form.as_p }}
                <button type="submit" class="btn btn-gold">Lock and Sign Final Grade</button>
            </form>
        </div>
    </div>
</body>
</html>
'''
}

print("⚙️ Synthesizing Complete Production SIST System Module Files...")
for path, text in files_to_create.items():
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.strip())
print("🚀 COMPLETE CODE ARCHITECTURE BUILT!")