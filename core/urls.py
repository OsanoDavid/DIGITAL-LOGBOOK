from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admins/', views.admin_login_view, name='admin_login'),
    path('admins/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard_legacy'),
    path('admin-create-user/', views.admin_create_user_view, name='admin_create_user'),
    path('debug/login-supervisor/', views.debug_login_supervisor, name='debug_login_supervisor'),

    # highlight-start
    # Route for adding a new log mapped to the student's current period
    path('log/create/<int:period_id>/', views.create_log_view, name='create_log'),
    # highlight-end
    
    path('profile/update-meta/', views.update_profile_meta, name='update_profile_meta'),
    path('log/edit/<int:log_id>/', views.edit_week_log, name='edit_log'),
    path('log/review/supervisor/<int:log_id>/', views.supervisor_review_log, name='supervisor_review'),
    path('log/sign/lecturer/<int:log_id>/', views.lecturer_sign_log, name='lecturer_sign'),
    path('grading/final/<int:period_id>/', views.final_grading_view, name='final_grading'),
    path('assessment/submit/<int:period_id>/', views.submit_assessment_form, name='submit_assessment_form'),
    path('info/<str:page_name>/', views.info_page_view, name='info_page'),
]