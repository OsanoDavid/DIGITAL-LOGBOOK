from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admins/', views.admin_login_view, name='admin_login'),
    path('admins/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard_legacy'),
    path('admin-create-user/', views.admin_create_user_view, name='admin_create_user'),
    path('admin/create-supervisor-request/', views.admin_create_supervisor_from_request_view, name='admin_create_supervisor_from_request'),
    path('admin/notification/<int:notif_id>/read/', views.mark_admin_notification_read, name='mark_admin_notification_read'),
    path('admin/users/<int:user_id>/manage/', views.admin_manage_user_view, name='admin_manage_user'),
    path('debug/login-supervisor/', views.debug_login_supervisor, name='debug_login_supervisor'),

    # highlight-start
    # Route for adding a new log mapped to the student's current period
    path('log/create/<int:period_id>/', views.create_log_view, name='create_log'),
    path('log/download-all/<int:period_id>/', views.download_all_logs_view, name='download_all_logs'),
    path('log/download/<int:log_id>/', views.download_week_log_view, name='download_log'),
    # highlight-end
    
    path('profile/update-meta/', views.update_profile_meta, name='update_profile_meta'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('log/edit/<int:log_id>/', views.edit_week_log, name='edit_log'),
    path('log/review/supervisor/<int:log_id>/', views.supervisor_review_log, name='supervisor_review'),
    path('log/sign/lecturer/<int:log_id>/', views.lecturer_sign_log, name='lecturer_sign'),
    path('grading/final/<int:period_id>/', views.final_grading_view, name='final_grading'),
    path('assessment/submit/<int:period_id>/', views.submit_assessment_form, name='submit_assessment_form'),
    path('report/review/<int:period_id>/', views.review_final_report, name='review_final_report'),
    path('info/<str:page_name>/', views.info_page_view, name='info_page'),
]