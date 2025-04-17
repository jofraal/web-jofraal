from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group

class AdminUserCreationForm(UserCreationForm):
    """Form for creating new admin users with specific permission groups"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    admin_group = forms.ModelChoiceField(
        queryset=Group.objects.filter(
            name__in=['SuperAdmins', 'ProductManagers', 'OrderManagers', 'CustomerSupportManagers']
        ),
        required=True,
        label='Nivel de Administrador'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'admin_group']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        
        # Make user a superuser only if they're in the SuperAdmins group
        if self.cleaned_data.get('admin_group').name == 'SuperAdmins':
            user.is_superuser = True
        
        if commit:
            user.save()
            # Add user to the selected admin group
            self.cleaned_data.get('admin_group').user_set.add(user)
        
        return user

class AdminUserEditForm(forms.ModelForm):
    """Form for editing existing admin users"""
    email = forms.EmailField(required=True)
    admin_group = forms.ModelChoiceField(
        queryset=Group.objects.filter(
            name__in=['SuperAdmins', 'ProductManagers', 'OrderManagers', 'CustomerSupportManagers']
        ),
        required=True,
        label='Nivel de Administrador'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'admin_group']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial value for admin_group if user belongs to any admin group
        if self.instance.pk:
            admin_groups = Group.objects.filter(
                name__in=['SuperAdmins', 'ProductManagers', 'OrderManagers', 'CustomerSupportManagers'],
                user=self.instance
            )
            if admin_groups.exists():
                self.fields['admin_group'].initial = admin_groups.first()
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Update superuser status based on admin group
        user.is_superuser = (self.cleaned_data.get('admin_group').name == 'SuperAdmins')
        
        if commit:
            user.save()
            
            # Remove user from all admin groups
            admin_groups = Group.objects.filter(
                name__in=['SuperAdmins', 'ProductManagers', 'OrderManagers', 'CustomerSupportManagers']
            )
            for group in admin_groups:
                group.user_set.remove(user)
            
            # Add user to the selected admin group
            self.cleaned_data.get('admin_group').user_set.add(user)
        
        return user