import importlib
import os
from unittest.mock import patch

from django.contrib.auth import authenticate
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import ProfileUpdateForm, SISTRegistrationForm
from .models import AdminNotification, User, AttachmentPeriod, WeeklyLog
from .views import _ensure_period_assignments


class DatabaseSettingsTests(TestCase):
    def test_dj_database_url_dependency_is_available(self):
        self.assertTrue(importlib.util.find_spec('dj_database_url'))

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

    def test_prefers_postgres_when_a_valid_database_url_exists(self):
        with patch.dict(os.environ, {'DEBUG': 'True', 'USE_SQLITE': 'true', 'SQLITE_DB_PATH': '/tmp/custom-db.sqlite3', 'DATABASE_URL': 'postgres://user:pass@localhost:5432/db'}, clear=False):
            settings_module = importlib.import_module('sist_project.settings')
            reloaded_module = importlib.reload(settings_module)

            self.assertEqual(reloaded_module.DATABASES['default']['ENGINE'], 'django.db.backends.postgresql')
            self.assertEqual(reloaded_module.DATABASES['default']['NAME'], 'db')

    def test_render_falls_back_to_sqlite_for_a_legacy_database_name(self):
        with patch.dict(os.environ, {
            'DEBUG': 'False',
            'RENDER': 'true',
            'DATABASE_URL': 'dhangongo',
            'SQLITE_DB_PATH': '/tmp/render-db.sqlite3',
        }, clear=False):
            os.environ.pop('USE_SQLITE', None)
            settings_module = importlib.import_module('sist_project.settings')
            reloaded_module = importlib.reload(settings_module)

            self.assertEqual(reloaded_module.DATABASES['default']['ENGINE'], 'django.db.backends.sqlite3')
            self.assertEqual(reloaded_module.DATABASES['default']['NAME'], '/tmp/render-db.sqlite3')


class MediaUploadSettingsTests(TestCase):
    def test_profile_photo_field_uses_plain_file_storage(self):
        field = User._meta.get_field('profile_photo')

        self.assertEqual(field.get_internal_type(), 'FileField')
        self.assertEqual(ProfileUpdateForm.base_fields['profile_photo'].__class__.__name__, 'FileField')


class RegistrationFlowTests(TestCase):
    def test_student_can_update_attachment_organization(self):
        student = User.objects.create_user(
            username='STU-ORG-001',
            password='Pass1234!',
            role='STUDENT',
            institution_or_company='Original Organization',
        )
        period = AttachmentPeriod.objects.create(
            student=student,
            start_date='2026-01-01',
            field_supervisor_organization='Original Organization',
        )

        self.client.force_login(student)
        response = self.client.post(reverse('core:dashboard'), {
            'organization_update_form': '1',
            'institution_or_company': 'Updated Organization',
        })

        self.assertRedirects(response, reverse('core:dashboard'))
        student.refresh_from_db()
        period.refresh_from_db()
        self.assertEqual(student.institution_or_company, 'Updated Organization')
        self.assertEqual(period.field_supervisor_organization, 'Updated Organization')

        dashboard = self.client.get(reverse('core:dashboard'))
        self.assertContains(dashboard, 'list="organization_options"')
        self.assertContains(dashboard, 'name="field_supervisor_organization" list="organization_options"')
        self.assertContains(dashboard, 'ICT Authority Nairobi')

    def test_organization_change_reassigns_matching_supervisor_and_lecturer(self):
        student = User.objects.create_user(
            username='STU-ORG-002',
            password='Pass1234!',
            role='STUDENT',
            institution_or_company='ICT Authority Nairobi',
            course='Computer Science',
        )
        ict_supervisor = User.objects.create_user(
            username='SUP-ICT-001',
            password='Pass1234!',
            role='SUPERVISOR',
            institution_or_company='ICT Authority Nairobi',
        )
        ict_lecturer = User.objects.create_user(
            username='LEC-ICT-001',
            password='Pass1234!',
            role='LECTURER',
            institution_or_company='ICT Authority Nairobi',
            course='Computer Science',
        )
        safaricom_supervisor = User.objects.create_user(
            username='SUP-SAF-001',
            password='Pass1234!',
            role='SUPERVISOR',
            institution_or_company='Safaricom PLC',
        )
        safaricom_lecturer = User.objects.create_user(
            username='LEC-SAF-001',
            password='Pass1234!',
            role='LECTURER',
            institution_or_company='Safaricom PLC',
            course='Computer Science',
        )
        period = AttachmentPeriod.objects.create(
            student=student,
            supervisor=ict_supervisor,
            lecturer=ict_lecturer,
            start_date='2026-01-01',
        )

        self.client.force_login(student)
        response = self.client.post(reverse('core:dashboard'), {
            'organization_update_form': '1',
            'institution_or_company': 'Safaricom PLC',
        })

        self.assertRedirects(response, reverse('core:dashboard'))
        period.refresh_from_db()
        self.assertEqual(period.supervisor, safaricom_supervisor)
        self.assertEqual(period.lecturer, safaricom_lecturer)

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

    def test_attachment_admin_dashboard_is_available_for_attachment_admin_users(self):
        admin_user = User.objects.create_user(
            username='ATTADMIN01',
            password='Pass1234!',
            role='ATTACHMENT_ADMIN',
            first_name='Attachment',
            last_name='Administrator',
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse('core:admin_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Attachment Administrator')

    def test_attachment_admin_cannot_create_system_admin_accounts(self):
        attachment_admin = User.objects.create_user(
            username='ATTADMIN02',
            password='Pass1234!',
            role='ATTACHMENT_ADMIN',
            first_name='Attachment',
            last_name='Officer',
        )

        self.client.force_login(attachment_admin)
        response = self.client.post(reverse('core:admin_create_user'), {
            'full_name': 'System Admin',
            'username': 'SYSADM999',
            'email': 'sysadm@example.com',
            'role': 'ADMIN',
            'phone_number': '+254700000199',
            'institution_or_company': 'Kisii University',
            'course': 'Computer Science',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='SYSADM999').exists())

    def test_attachment_admin_cannot_promote_an_existing_user_to_system_admin(self):
        attachment_admin = User.objects.create_user(
            username='ATTADMIN03',
            password='Pass1234!',
            role='ATTACHMENT_ADMIN',
            first_name='Attachment',
            last_name='Officer',
        )
        student = User.objects.create_user(
            username='STU800',
            password='Pass1234!',
            role='STUDENT',
            first_name='Test',
            last_name='Student',
        )

        self.client.force_login(attachment_admin)
        response = self.client.post(reverse('core:admin_manage_user', args=[student.id]), {
            'action': 'edit',
            'full_name': 'Test Student',
            'email': 'student@example.com',
            'phone_number': '+254700000200',
            'institution_or_company': 'Kisii University',
            'course': 'Computer Science',
            'role': 'ADMIN',
        })

        self.assertEqual(response.status_code, 403)
        student.refresh_from_db()
        self.assertEqual(student.role, 'STUDENT')

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

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
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
            'workspace_role': 'Internal Academic University Assessor',
            'national_id': '12345678',
            'specialization': 'Computer Science',
            'university': 'Kisii University',
            'faculty': 'School of Information Sciences & Technology',
            'department': 'Computing Sciences',
            'university_email': 'grace@kisiiuniversity.ac.ke',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='LEC999').exists())
        lecturer = User.objects.get(username='LEC999')
        self.assertEqual(lecturer.lecturer_profile.department, 'Computing Sciences')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Account Invitation', mail.outbox[0].subject)
        self.assertIn('grace@example.com', mail.outbox[0].to)

    @patch('core.views._send_new_account_email', side_effect=RuntimeError('SMTP unavailable'))
    def test_account_creation_redirects_when_email_delivery_fails(self, _send_email):
        admin_user = User.objects.create_user(
            username='ADMIN05', password='Pass1234!', role='ADMIN', first_name='System', last_name='Administrator',
        )
        self.client.force_login(admin_user)

        response = self.client.post(reverse('core:admin_create_user'), {
            'full_name': 'Email Failure Lecturer', 'username': 'LEC998', 'email': 'failure@example.com',
            'role': 'LECTURER', 'phone_number': '+254700000098', 'course': 'Computer Science',
            'workspace_role': 'Internal Academic University Assessor', 'national_id': '12345679',
            'specialization': 'Computer Science', 'university': 'Kisii University',
            'faculty': 'School of Information Sciences & Technology', 'department': 'Computing Sciences',
            'university_email': 'failure@kisiiuniversity.ac.ke',
            'password': 'SecurePass123!', 'confirm_password': 'SecurePass123!',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('core:admin_dashboard'))
        self.assertTrue(User.objects.filter(username='LEC998').exists())
        self.assertContains(response, 'Account created, but the invitation email could not be sent.')

    def test_supervisor_request_creates_in_app_notification_without_admin_email(self):
        attachment_admin = User.objects.create_user(
            username='ATTADMIN04', password='Pass1234!', role='ATTACHMENT_ADMIN', first_name='Attachment', last_name='Officer',
        )
        student = User.objects.create_user(
            username='STU999', password='Pass1234!', role='STUDENT', first_name='Requesting', last_name='Student',
            institution_or_company='Kisii University', course='Computer Science',
        )
        self.client.force_login(student)

        response = self.client.post(reverse('core:dashboard'), {
            'supervisor_update_form': '1', 'field_supervisor_name': 'Jane Supervisor',
            'field_supervisor_email': 'jane.supervisor@example.com', 'field_supervisor_phone': '+254700000097',
            'field_supervisor_organization': 'Kisii University',
        })

        self.assertEqual(response.status_code, 302)
        notification = AdminNotification.objects.get(recipient=attachment_admin)
        self.assertIn('Jane Supervisor', notification.message)
        self.assertIn('panel=supervisors-panel', notification.action_url)

    def test_registration_view_blocks_new_signups_when_system_registration_is_locked(self):
        from .models import SystemSettings

        SystemSettings.objects.update_or_create(defaults={'registration_enabled': False}, id=1)

        response = self.client.post(reverse('core:register'), {
            'username': 'IN14/00001/22',
            'full_name': 'Jane Doe',
            'email': 'jane2@example.com',
            'role': 'STUDENT',
            'phone_number': '+254700000001',
            'institution_or_company': 'ICT Authority',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('core:login'), response.url)
        self.assertIn('registration_closed=1', response.url)
        self.assertFalse(User.objects.filter(username='IN14/00001/22').exists())

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

    def test_registration_number_login_is_case_insensitive_and_normalized(self):
        User.objects.create_user(
            username='IN14-00000-22',
            email='jane.lower@example.com',
            password='securepass123',
            role='STUDENT',
            first_name='Jane',
            last_name='Doe',
        )
        self.assertTrue(authenticate(username='in14/00000/22', password='securepass123'))

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

    def test_supervisor_registration_uses_its_staff_id_and_allows_shared_company(self):
        User.objects.create_user(
            username='SUP-001',
            email='existing.supervisor@example.com',
            phone_number='+254700000010',
            password='SecurePass123!',
            role='SUPERVISOR',
            institution_or_company='Shared Company',
        )

        form = SISTRegistrationForm(data={
            'username': 'SUP-002',
            'full_name': 'New Supervisor',
            'email': 'new.supervisor@example.com',
            'role': 'SUPERVISOR',
            'phone_number': '+254700000011',
            'institution_or_company': 'Shared Company',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().username, 'SUP-002')

    def test_registration_rejects_only_a_duplicate_phone_when_other_details_match(self):
        User.objects.create_user(
            username='LEC-001',
            email='existing.lecturer@example.com',
            phone_number='+254 700 000 012',
            password='SecurePass123!',
            role='LECTURER',
            course='Computer Science',
        )

        form = SISTRegistrationForm(data={
            'username': 'LEC-002',
            'full_name': 'New Lecturer',
            'email': 'new.lecturer@example.com',
            'role': 'LECTURER',
            'phone_number': '+254700000012',
            'course': 'Computer Science',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('phone_number', form.errors)

    def test_registration_view_rejects_duplicate_registration_details(self):
        User.objects.create_user(
            username='IN14/00000/22',
            email='duplicate@example.com',
            password='SecurePass123!',
            role='STUDENT',
            first_name='Existing',
            last_name='Student',
        )

        response = self.client.post(reverse('core:register'), {
            'username': 'IN14/00000/22',
            'full_name': 'New Student',
            'email': 'duplicate@example.com',
            'role': 'STUDENT',
            'phone_number': '+254700000001',
            'institution_or_company': 'Kisii County Referral Hospital',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that Registration Number / Staff ID already exists in the database.')
        self.assertContains(response, 'An account with this email already exists in the database.')
        self.assertEqual(User.objects.filter(username='IN14/00000/22').count(), 1)

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
            email='student205@example.com',
        )

        self.client.force_login(admin_user)
        response = self.client.post(reverse('core:admin_manage_user', args=[target_user.id]), {
            'action': 'reset_password',
            'new_password': 'NewPass123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(authenticate(username='STU205', password='NewPass123!'))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_admin_can_resend_an_invitation_email(self):
        admin_user = User.objects.create_user(
            username='ADMIN04',
            password='Pass1234!',
            role='ADMIN',
            first_name='System',
            last_name='Administrator',
        )
        target_user = User.objects.create_user(
            username='STU206',
            password='OldPass123!',
            role='STUDENT',
            first_name='New',
            last_name='Student',
            email='student206@example.com',
        )

        self.client.force_login(admin_user)
        response = self.client.post(reverse('core:admin_manage_user', args=[target_user.id]), {
            'action': 'resend_invite',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Account Invitation', mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ['student206@example.com'])
