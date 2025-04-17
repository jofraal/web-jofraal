from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .admin_forms import AdminUserCreationForm, AdminUserEditForm
from .admin_groups import create_admin_groups, remove_user_from_admin_groups
from django.core.paginator import Paginator

# Helper function to check if user is a superadmin
def is_superadmin(user):
    return user.is_authenticated and user.is_superuser

# Helper function to check if user is any type of admin
def is_admin(user):
    if not user.is_authenticated or not user.is_staff:
        return False
    admin_groups = ['SuperAdmins', 'ProductManagers', 'OrderManagers', 'CustomerSupportManagers']
    return user.groups.filter(name__in=admin_groups).exists()

@login_required
@user_passes_test(is_superadmin)
def admin_dashboard(request):
    """Dashboard for admin users with links to various admin functions"""
    # Ensure admin groups exist
    create_admin_groups()
    
    # Get counts for different types of admin users
    admin_counts = {
        'SuperAdmins': User.objects.filter(groups__name='SuperAdmins').count(),
        'ProductManagers': User.objects.filter(groups__name='ProductManagers').count(),
        'OrderManagers': User.objects.filter(groups__name='OrderManagers').count(),
        'CustomerSupportManagers': User.objects.filter(groups__name='CustomerSupportManagers').count(),
    }
    
    return render(request, 'users/admin/dashboard.html', {
        'admin_counts': admin_counts,
    })

@login_required
@user_passes_test(is_superadmin)
def admin_user_list(request):
    """List all admin users with pagination"""
    admin_groups = ['SuperAdmins', 'ProductManagers', 'OrderManagers', 'CustomerSupportManagers']
    admin_users = User.objects.filter(groups__name__in=admin_groups).distinct()
    
    paginator = Paginator(admin_users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'users/admin/user_list.html', {
        'page_obj': page_obj,
    })

@login_required
@user_passes_test(is_superadmin)
def admin_user_create(request):
    """Create a new admin user"""
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Administrador creado exitosamente')
            return redirect('users:admin_user_list')
    else:
        form = AdminUserCreationForm()
    
    return render(request, 'users/admin/user_form.html', {
        'form': form,
        'title': 'Crear Nuevo Administrador',
    })

@login_required
@user_passes_test(is_superadmin)
def admin_user_edit(request, user_id):
    """Edit an existing admin user"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Administrador actualizado exitosamente')
            return redirect('users:admin_user_list')
    else:
        form = AdminUserEditForm(instance=user)
    
    return render(request, 'users/admin/user_form.html', {
        'form': form,
        'title': f'Editar Administrador: {user.username}',
        'user': user,
    })

@login_required
@user_passes_test(is_superadmin)
def admin_user_delete(request, user_id):
    """Delete an admin user (remove admin privileges)"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Remove user from all admin groups
        remove_user_from_admin_groups(user)
        messages.success(request, f'Se han eliminado los privilegios de administrador para {user.username}')
        return redirect('users:admin_user_list')
    
    return render(request, 'users/admin/user_confirm_delete.html', {
        'user': user,
    })