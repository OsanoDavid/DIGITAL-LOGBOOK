from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('debug/login-supervisor/', views.debug_login_supervisor, name='debug_login_supervisor'),

    # highlight-start
    # Route for adding a new log mapped to the student's current period
    path('log/create/<int:period_id>/', views.create_log_view, name='create_log'),
    # highlight-end
    
    path('log/edit/<int:log_id>/', views.edit_week_log, name='edit_log'),
    path('log/review/supervisor/<int:log_id>/', views.supervisor_review_log, name='supervisor_review'),
    path('log/sign/lecturer/<int:log_id>/', views.lecturer_sign_log, name='lecturer_sign'),
    path('grading/final/<int:period_id>/', views.final_grading_view, name='final_grading'),
]