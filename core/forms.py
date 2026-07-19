from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .auth_utils import normalize_username
from .models import User, WeeklyLog, AttachmentPeriod

COURSE_CHOICES = [
    ('', 'Select course / programme'),
    ('Computer Science', 'Computer Science'),
    ('Applied Computer Science', 'Applied Computer Science'),
    ('Software Engineering', 'Software Engineering'),
    ('Information Technology', 'Information Technology'),
]


class SISTRegistrationForm(forms.ModelForm):
    full_name = forms.CharField(required=True, label='Full Name')
    password = forms.CharField(widget=forms.PasswordInput, label='Create Password', strip=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirm Password', strip=False)
    institution_or_company = forms.CharField(required=False, label='Company or Organization', help_text='Required for students and supervisors.')
    course = forms.ChoiceField(choices=COURSE_CHOICES, required=False, label='Course / Programme')

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'phone_number', 'institution_or_company', 'course', 'profile_photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields['username'].help_text = ''
        self.fields['email'].required = True
        self.fields['institution_or_company'].widget.attrs.update({'placeholder': 'e.g. Safaricom, Kisii County Hospital'})
        self.fields['course'].widget.attrs.update({'class': 'form-control'})

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        role = self.data.get('role', 'STUDENT')

        if role in ('SUPERVISOR', 'LECTURER'):
            provided_username = (self.data.get('username') or '').strip()
            if provided_username:
                if User.objects.filter(username__iexact=provided_username).exists():
                    raise forms.ValidationError('An account with this username already exists.')
                return provided_username

            email = self.data.get('email', '').strip().lower()
            if not email:
                raise forms.ValidationError('Email is required.')
            if User.objects.filter(username__iexact=email).exists():
                raise forms.ValidationError('An account with this email already exists.')
            return email

        normalized = normalize_username(username)
        if not normalized:
            raise forms.ValidationError('A registration number is required.')

        normalized_lookup = normalized.lower()
        for existing in User.objects.values_list('username', flat=True):
            if existing and normalize_username(existing).lower() == normalized_lookup:
                raise forms.ValidationError('A user with that registration number already exists.')
        return normalized

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        role = self.data.get('role', 'STUDENT')
        if not email:
            raise forms.ValidationError('Email is required.')

        if role in ('SUPERVISOR', 'LECTURER'):
            if User.objects.filter(username__iexact=email).exists():
                raise forms.ValidationError('An account with this email already exists.')
        else:
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError('An account with this email already exists.')
            if User.objects.filter(username__iexact=email).exists():
                raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        role = cleaned_data.get('role')
        institution_or_company = (cleaned_data.get('institution_or_company') or '').strip()
        course = cleaned_data.get('course')

        if role in ('SUPERVISOR', 'LECTURER'):
            email = (cleaned_data.get('email') or '').strip().lower()
            if not email:
                raise forms.ValidationError({'email': 'Email address is required.'})

            username_value = (cleaned_data.get('username') or '').strip()
            if username_value:
                cleaned_data['username'] = username_value
            else:
                cleaned_data['username'] = email

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError({'confirm_password': 'Passwords do not match.'})

        if role in ('STUDENT', 'SUPERVISOR'):
            if not institution_or_company:
                raise forms.ValidationError({'institution_or_company': 'Company or organization is required for students and supervisors.'})

        if role in ('STUDENT', 'LECTURER'):
            inferred_course = None
            if role == 'STUDENT':
                inferred_course = User.infer_course_from_registration(self.cleaned_data.get('username'))

            if not course and not inferred_course:
                raise forms.ValidationError({'course': 'Please select the course or programme.'})

            if inferred_course:
                cleaned_data['course'] = inferred_course

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name', '')
        if full_name:
            parts = full_name.strip().split()
            user.first_name = parts[0]
            user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
        user.institution_or_company = (self.cleaned_data.get('institution_or_company') or '').strip() or user.institution_or_company
        selected_course = self.cleaned_data.get('course')
        if selected_course:
            user.course = selected_course
        elif user.role == 'STUDENT':
            user.course = User.infer_course_from_registration(self.cleaned_data.get('username'))
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


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


class ProfileUpdateForm(forms.ModelForm):
    avatar_color = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
        label='Profile Color',
        required=False,
        help_text='Choose a default color for your profile avatar'
    )
    profile_photo = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        label='Profile Picture',
        required=False,
        help_text='Upload a profile picture (optional)'
    )

    class Meta:
        model = User
        fields = ['avatar_color', 'profile_photo']