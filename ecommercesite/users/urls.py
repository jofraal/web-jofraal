from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from . import admin_views  # Importar las vistas de administración
from social_django import urls as social_urls  # Importación explícita
from django.urls import reverse_lazy

app_name = 'users'

urlpatterns = [
    # User authentication routes
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('orders/', views.order_history, name='order_history'),
    
    # Password reset routes
    path('password-reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='users/password_reset.html',
            email_template_name='users/password_reset_email.html',
            subject_template_name='users/password_reset_subject.txt',
            success_url=reverse_lazy('users:password_reset_done')
        ), 
        name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url=reverse_lazy('users:password_reset_complete')
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Admin management routes
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', admin_views.admin_user_list, name='admin_user_list'),
    path('admin/users/create/', admin_views.admin_user_create, name='admin_user_create'),
    path('admin/users/<int:user_id>/edit/', admin_views.admin_user_edit, name='admin_user_edit'),
    path('admin/users/<int:user_id>/delete/', admin_views.admin_user_delete, name='admin_user_delete'),
    
    # Social authentication routes
    path('auth/', include('social_django.urls', namespace='social_auth')),

    # Marketing email route
    path('send_marketing_email/', views.send_marketing_email, name='send_marketing_email'),
]