import os

APP_NAME = "core"

files_to_create = {
    # 1. MULTI-ROLE MODELS PIPELINE
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
    is_finalized = models.BooleanField(default=False)
    
    supervisor_marks = models.FloatField(null=True, blank=True)
    supervisor_comment = models.TextField(blank=True, null=True)
    supervisor_signed = models.BooleanField(default=False)
    
    lecturer_grade = models.CharField(max_length=2, blank=True, null=True)
    lecturer_marks = models.FloatField(null=True, blank=True)
    lecturer_comment = models.TextField(blank=True, null=True)
    lecturer_signed = models.BooleanField(default=False)

    def __str__(self):
        return f"SIST Logbook - {self.student.username}"

class WeeklyLog(models.Model):
    profile = models.ForeignKey(AttachmentPeriod, on_delete=models.CASCADE, related_name='weekly_logs')
    week_number = models.PositiveIntegerField()
    
    monday_activity = models.TextField(blank=True, null=True)
    tuesday_activity = models.TextField(blank=True, null=True)
    wednesday_activity = models.TextField(blank=True, null=True)
    thursday_activity = models.TextField(blank=True, null=True)
    friday_activity = models.TextField(blank=True, null=True)
    
    is_submitted = models.BooleanField(default=False)
    supervisor_approved = models.BooleanField(default=False)
    supervisor_comment = models.TextField(blank=True, null=True)
    
    lecturer_approved = models.BooleanField(default=False)
    lecturer_comment = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('profile', 'week_number')
        ordering = ['week_number']
''',

    # 2. DATA CAPTURE AND VALIDATION FORMS
    f"{APP_NAME}/forms.py": '''from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, WeeklyLog

class SISTRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'role', 'phone_number')

class SISTLoginForm(AuthenticationForm):
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial='STUDENT', widget=forms.Select(attrs={'class': 'form-select'}))

class LogEntryForm(forms.ModelForm):
    class Meta:
        model = WeeklyLog
        fields = ['monday_activity', 'tuesday_activity', 'wednesday_activity', 'thursday_activity', 'friday_activity']
        widgets = {
            f'{day}_activity': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}) for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        }
''',

    # 3. DISPATCHER VIEWS 
    f"{APP_NAME}/views.py": '''from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import AttachmentPeriod, WeeklyLog
from .forms import SISTRegistrationForm, SISTLoginForm, LogEntryForm

def login_view(request):
    if request.method == 'POST':
        form = SISTLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.role != request.POST.get('role'):
                form.add_error(None, "Selected role does not match system account configurations.")
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
        return render(request, 'core/student_dashboard.html', {'period': period, 'logs': period.weekly_logs.all()})
    return render(request, 'core/staff_dashboard.html')

@login_required
def edit_week_log(request, log_id):
    log = get_object_or_404(WeeklyLog, id=log_id, profile__student=request.user)
    if log.supervisor_approved:
        return HttpResponseForbidden("Locked entries cannot be modified.")
    if request.method == 'POST':
        form = LogEntryForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = LogEntryForm(instance=log)
    return render(request, 'core/edit_log.html', {'form': form, 'log': log})
''',

    # 4. APP SYSTEM URL ROUTING
    f"{APP_NAME}/urls.py": '''from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('log/edit/<int:log_id>/', views.edit_week_log, name='edit_log'),
]
''',

    # 5. KISII UNIVERSITY BRANDED EXTERNAL CSS ASSET
    f"static/css/sist_style.css": '''
:root { --kisii-blue: #0f4c81; --sist-gold: #f4a261; --slate: #1e293b; --bg: #f8fafc; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--slate); margin: 0; }
header { background: #fff; border-bottom: 4px solid var(--kisii-blue); padding: 15px 5%; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
.main-container { max-width: 1100px; margin: 40px auto; padding: 0 20px; }
.card { background: #fff; border-radius: 8px; border: 1px solid #e2e8f0; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.01); }
.btn-primary { background: var(--kisii-blue); color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; text-decoration: none; }
.btn-gold { background: var(--sist-gold); color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; text-decoration: none; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: left; }
th { background: var(--kisii-blue); color: white; }
''',

    # 6. SIGN-IN INTERFACE TEMPLATE
    f"templates/core/login.html": '''<!DOCTYPE html>
<html>
<head>
    <title>SIST Logbook Portal - Sign In</title>
    <link rel="stylesheet" href="/static/css/sist_style.css">
</head>
<body>
    <header>
        <div><h2 style="margin:0; color: #0f4c81;">KISII UNIVERSITY</h2><small style="color:#f4a261; font-weight:bold;">School of Information Sciences & Technology</small></div>
    </header>
    <div class="main-container" style="max-width: 450px; margin-top: 80px;">
        <div class="card">
            <h3 style="margin-top:0; color:#0f4c81;">SIST Digital Attachment Logbook</h3>
            <form method="POST">
                {% csrf_token %}
                {{ form.as_p }}
                <button type="submit" class="btn-gold" style="width: 100%; margin-top: 10px;">Access Account</button>
            </form>
            <p style="margin-top:15px; font-size:14px; text-align:center;">New Student? <a href="{% url 'register' %}">Create Account here</a></p>
        </div>
    </div>
</body>
</html>
''',

    # 7. REGISTRATION TEMPLATE
    f"templates/core/register.html": '''<!DOCTYPE html>
<html>
<head>
    <title>SIST Logbook - Registration</title>
    <link rel="stylesheet" href="/static/css/sist_style.css">
</head>
<body>
    <div class="main-container" style="max-width: 500px; margin-top: 50px;">
        <div class="card">
            <h2 style="color:#0f4c81; margin-top:0;">SIST Account Registration</h2>
            <form method="POST">
                {% csrf_token %}
                {{ form.as_p }}
                <button type="submit" class="btn-primary" style="width:100%;">Complete Sign Up</button>
            </form>
        </div>
    </div>
</body>
</html>
''',

    # 8. STUDENT LOGBOOK OVERVIEW WORKSPACE
    f"templates/core/student_dashboard.html": '''<!DOCTYPE html>
<html>
<head>
    <title>SIST Dashboard</title>
    <link rel="stylesheet" href="/static/css/sist_style.css">
</head>
<body>
    <header>
        <div><h2>KISII UNIVERSITY - SIST</h2><p style="margin:0;">Active Student Workspace</p></div>
        <a href="{% url 'logout' %}" class="btn-primary" style="background:#ef4444;">Sign Out</a>
    </header>
    <div class="main-container">
        <div class="card">
            <h3>Weekly Logs Matrices (14 Weeks Attachment)</h3>
            <table>
                <thead>
                    <tr><th>Week Number</th><th>Verification Status</th><th>Supervisor Action</th><th>Actions</th></tr>
                </thead>
                <tbody>
                    {% for log in logs %}
                    <tr>
                        <td><strong>Week {{ log.week_number }}</strong></td>
                        <td>{% if log.supervisor_approved %}<span style="color:green; font-weight:bold;">Verified & Signed</span>{% else %}<span style="color:#b45309;">Draft Status</span>{% endif %}</td>
                        <td>{{ log.supervisor_comment|default:"No evaluations added yet" }}</td>
                        <td>
                            {% if not log.supervisor_approved %}
                                <a href="{% url 'edit_log' log.id %}" class="btn-gold" style="padding:5px 12px; font-size:13px;">Fill Log</a>
                            {% else %}
                                <button class="btn-primary" style="padding:5px 12px; font-size:13px; background:#64748b;" onclick="window.print()">Download Log</button>
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

    # 9. EDIT WEEK LOG TEMPLATE
    f"templates/core/edit_log.html": '''<!DOCTYPE html>
<html>
<head>
    <title>Edit Week Log</title>
    <link rel="stylesheet" href="/static/css/sist_style.css">
</head>
<body>
    <div class="main-container" style="max-width: 700px;">
        <div class="card">
            <h2 style="color:#0f4c81; margin-top:0;">Record Work Matrix: Week {{ log.week_number }}</h2>
            <form method="POST">
                {% csrf_token %}
                {{ form.as_p }}
                <div style="margin-top:20px;">
                    <button type="submit" class="btn-primary">Save Weekly Records</button>
                    <a href="{% url 'dashboard' %}" class="btn-gold" style="background:#64748b;">Back to Dashboard</a>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''
}

print("⚙️ Auto-structuring SIST Project Components...")
for path, data in files_to_create.items():
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data.strip())
print("🚀 Component structuring complete!")