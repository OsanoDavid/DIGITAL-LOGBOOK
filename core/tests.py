from django.contrib.auth import authenticate
from django.test import TestCase
from django.urls import reverse

from .forms import SISTRegistrationForm
from .models import User, AttachmentPeriod, WeeklyLog
from .views import _ensure_period_assignments


class RegistrationFlowTests(TestCase):
    def test_registration_form_accepts_template_field_names(self):
        form = SISTRegistrationForm(
            data={
                'username': 'IN14/00000/22',
                'full_name': 'Jane Doe',
                'email': 'jane@example.com',
                'role': 'STUDENT',
                'phone_number': '+254700000000',
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

    def test_period_assignment_falls_back_to_first_supervisor_when_no_company_match(self):
        student = User.objects.create_user(
            username='STU200',
            password='pass1234!',
            role='STUDENT',
            first_name='Ada',
            last_name='Student',
            institution_or_company='Kisii County Referral Hospital',
        )
        supervisor = User.objects.create_user(
            username='SUP200',
            password='pass1234!',
            role='SUPERVISOR',
            first_name='Ben',
            last_name='Supervisor',
            institution_or_company='Nairobi Hospital',
        )
        period = AttachmentPeriod.objects.create(student=student, start_date='2026-01-01')

        _ensure_period_assignments(period)

        self.assertEqual(period.supervisor, supervisor)

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

    def test_create_log_creates_only_the_next_missing_week(self):
        student = User.objects.create_user(
            username='STU202',
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
