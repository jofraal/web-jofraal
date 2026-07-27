from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from . import admin_views  # Importar las vistas de administración
from social_django import urls as social_urls  # Importación explícita
from django.urls import reverse_lazy
from .forms import CustomPasswordChangeForm, CustomSetPasswordForm  # Importar formularios personalizados

app_name = 'users'

urlpatterns = [
    # User authentication routes
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('orders/', views.order_history, name='order_history'),
    path('rate-product/<int:product_id>/', views.rate_product, name='rate_product'),
    path('addresses/', views.addresses, name='addresses'),
    path('add-address/', views.edit_address, name='add_address'),
    path('edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('set-default-address/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('payment-methods/', views.payment_methods, name='payment_methods'),
    path('refund-info/', views.refund_info, name='refund_info'),
    path('wishlists/', views.wishlists, name='wishlists'),
    path('account-settings/', views.account_settings, name='account_settings'),
    
    # API para ubicaciones (departamentos, provincias, distritos)
    path('api/get-departments/', views.get_departments_api, name='get_departments_api'),
    path('api/get-provinces/', views.get_provinces_api, name='get_provinces_api'),
    path('api/get-districts/', views.get_districts_api, name='get_districts_api'),
    
    # Password change route for authenticated users
    path('password-change/',
         auth_views.PasswordChangeView.as_view(
             template_name='users/password_change.html',
             form_class=CustomPasswordChangeForm,
             success_url=reverse_lazy('users:password_change_done')
         ),
         name='password_change'),
    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='users/password_change_done.html'
         ),
         name='password_change_done'),
         
    # Password reset routes (for forgotten passwords)
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
             form_class=CustomSetPasswordForm,
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
    
    # Las rutas API para ubicaciones ya están definidas arriba
]