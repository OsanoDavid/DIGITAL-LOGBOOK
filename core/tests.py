import importlib
import os
from unittest.mock import patch

from django.contrib.auth import authenticate
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .forms import SISTRegistrationForm
from .models import User, AttachmentPeriod, WeeklyLog
from .views import _ensure_period_assignments


class DatabaseSettingsTests(TestCase):
    def test_falls_back_to_sqlite_when_database_url_is_missing_in_debug_mode(self):
        with patch.dict(os.environ, {'DEBUG': 'True'}, clear=False):
            os.environ.pop('DATABASE_URL', None)
            settings_module = importlib.import_module('sist_project.settings')
            reloaded_module = importlib.reload(settings_module)

            self.assertEqual(
                reloaded_module.DATABASES['default']['ENGINE'],
                'django.db.backends.sqlite3',
            )

    def test_uses_sqlite_path_override_when_provided(self):
        with patch.dict(os.environ, {'DEBUG': 'True', 'SQLITE_DB_PATH': '/tmp/custom-db.sqlite3'}, clear=False):
            os.environ.pop('DATABASE_URL', None)
            settings_module = importlib.import_module('sist_project.settings')
            reloaded_module = importlib.reload(settings_module)

            self.assertEqual(reloaded_module.DATABASES['default']['NAME'], '/tmp/custom-db.sqlite3')


class RegistrationFlowTests(TestCase):
    def test_admin_dashboard_is_available_for_admin_users(self):
        admin_user = User.objects.create_user(
            username='ADMIN01',
            password='Pass1234!',
            role='ADMIN',
            first_name='System',
            last_name='Administrator',
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse('core:admin_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Control Center')

    def test_admin_dashboard_can_preselect_role_for_quick_create(self):
        admin_user = User.objects.create_user(
            username='ADMIN02',
            password='Pass1234!',
            role='ADMIN',
            first_name='System',
            last_name='Administrator',
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse('core:admin_dashboard') + '?role=LECTURER')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_role'], 'LECTURER')

    def test_admin_can_create_a_new_user_account(self):
        admin_user = User.objects.create_user(
            username='ADMIN02',
            password='Pass1234!',
            role='ADMIN',
            first_name='System',
            last_name='Administrator',
        )

        self.client.force_login(admin_user)
        response = self.client.post(reverse('core:admin_create_user'), {
            'full_name': 'Grace Lecturer',
            'username': 'LEC999',
            'email': 'grace@example.com',
            'role': 'LECTURER',
            'phone_number': '+254700000099',
            'institution_or_company': 'Kisii University',
            'course': 'Computer Science',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='LEC999').exists())

    def test_registration_form_accepts_template_field_names(self):
        form = SISTRegistrationForm(
            data={
                'username': 'IN14/00000/22',
                'full_name': 'Jane Doe',
                'email': 'jane@example.com',
                'role': 'STUDENT',
                'phone_number': '+254700000000',
                'institution_or_company': 'ICT Authority',
                'password': 'securepass123',
                'confirm_password': 'securepass123',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.course, 'Applied Computer Science')
        self.assertTrue(authenticate(username='IN14/00000/22', password='securepass123'))

    def test_student_registration_rejects_duplicate_registration_number_and_email(self):
        User.objects.create_user(
            username='IN14/00000/22',
            email='duplicate@example.com',
            password='SecurePass123!',
            role='STUDENT',
            first_name='Existing',
            last_name='Student',
        )

        form = SISTRegistrationForm(
            data={
                'username': 'IN14/00000/22',
                'full_name': 'New Student',
                'email': 'duplicate@example.com',
                'role': 'STUDENT',
                'phone_number': '+254700000001',
                'institution_or_company': 'Kisii County Referral Hospital',
                'password': 'SecurePass123!',
                'confirm_password': 'SecurePass123!',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('email', form.errors)

    def test_supervisor_registration_requires_company_or_organization(self):
        form = SISTRegistrationForm(
            data={
                'username': 'SUP14/00001/22',
                'full_name': 'Alex Supervisor',
                'email': 'alex@example.com',
                'role': 'SUPERVISOR',
                'phone_number': '+254700000001',
                'institution_or_company': '',
                'password': 'securepass123',
                'confirm_password': 'securepass123',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('institution_or_company', form.errors)
        self.assertIn('Company or organization', str(form.errors))

    def test_period_assignment_requires_matching_supervisor_company(self):
        student = User.objects.create_user(
            username='STU200',
            password='pass1234!',
            role='STUDENT',
            first_name='Ada',
            last_name='Student',
            institution_or_company='Kisii County Referral Hospital',
        )
        unmatched_supervisor = User.objects.create_user(
            username='SUP200',
            password='pass1234!',
            role='SUPERVISOR',
            first_name='Ben',
            last_name='Supervisor',
            institution_or_company='Nairobi Hospital',
        )
        matching_supervisor = User.objects.create_user(
            username='SUP201',
            password='pass1234!',
            role='SUPERVISOR',
            first_name='Clare',
            last_name='Supervisor',
            institution_or_company='Kisii County Referral Hospital',
        )
        period = AttachmentPeriod.objects.create(student=student, start_date='2026-01-01')

        _ensure_period_assignments(period)

        self.assertEqual(period.supervisor, matching_supervisor)
        self.assertNotEqual(period.supervisor, unmatched_supervisor)

    def test_supervisor_dashboard_shows_matching_student_logs(self):
        student = User.objects.create_user(
            username='STU201',
            password='pass1234!',
            role='STUDENT',
            first_name='Grace',
            last_name='Student',
            institution_or_company='Kisii County Referral Hospital',
        )
        supervisor = User.objects.create_user(
            username='SUP201',
            password='pass1234!',
            role='SUPERVISOR',
            first_name='Moses',
            last_name='Supervisor',
            institution_or_company='Kisii County Referral Hospital',
        )
        period = AttachmentPeriod.objects.create(student=student, start_date='2026-01-01')

        self.client.force_login(supervisor)
        response = self.client.get(reverse('core:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Grace Student')
        self.assertEqual(len(response.context['students']), 1)

    def test_period_assignment_requires_matching_lecturer_course(self):
        student = User.objects.create_user(
            username='STU202',
            password='pass1234!',
            role='STUDENT',
            first_name='Nina',
            last_name='Student',
            institution_or_company='Kisii County Referral Hospital',
            course='Computer Science',
        )
        lecturer = User.objects.create_user(
            username='LEC202',
            password='pass1234!',
            role='LECTURER',
            first_name='Diana',
            last_name='Lecturer',
            course='Applied Computer Science',
        )
        period = AttachmentPeriod.objects.create(student=student, start_date='2026-01-01')

        _ensure_period_assignments(period)

        self.assertIsNone(period.lecturer)
        self.assertNotEqual(period.lecturer, lecturer)

    def test_create_log_creates_only_the_next_missing_week(self):
        student = User.objects.create_user(
            username='STU203',
            password='pass1234!',
            role='STUDENT',
            first_name='Nina',
            last_name='Student',
            institution_or_company='Kisii County Referral Hospital',
        )
        period = AttachmentPeriod.objects.create(student=student, start_date='2026-01-01')

        self.client.force_login(student)
        self.client.get(reverse('core:create_log', args=[period.id]))

        logs = WeeklyLog.objects.filter(profile=period).order_by('week_number')
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs[0].week_number, 1)

    def test_lecturer_dashboard_lists_pending_reports_for_review(self):
        student = User.objects.create_user(
            username='STU204',
            password='pass1234!',
            role='STUDENT',
            first_name='Miriam',
            last_name='Student',
            institution_or_company='Kisii County Referral Hospital',
        )
        lecturer = User.objects.create_user(
            username='LEC204',
            password='pass1234!',
            role='LECTURER',
            first_name='Kevin',
            last_name='Lecturer',
            course='Computer Science',
        )
        period = AttachmentPeriod.objects.create(student=student, lecturer=lecturer, start_date='2026-01-01')
        period.final_report = SimpleUploadedFile('report.pdf', b'content', content_type='application/pdf')
        period.report_status = 'PENDING_REVIEW'
        period.save()

        self.client.force_login(lecturer)
        response = self.client.get(reverse('core:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertIn(period, response.context['pending_reports'])

    def test_admin_can_reset_a_user_password(self):
        admin_user = User.objects.create_user(
            username='ADMIN03',
            password='Pass1234!',
            role='ADMIN',
            first_name='System',
            last_name='Administrator',
        )
        target_user = User.objects.create_user(
            username='STU205',
            password='OldPass123!',
            role='STUDENT',
            first_name='Old',
            last_name='Student',
        )

        self.client.force_login(admin_user)
        response = self.client.post(reverse('core:admin_manage_user', args=[target_user.id]), {
            'action': 'reset_password',
            'new_password': 'NewPass123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(authenticate(username='STU205', password='NewPass123!'))
