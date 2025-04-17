from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import Profile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Usuario o Email',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ingresa tu usuario o correo',
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Ingresa tu contraseña',
            'class': 'form-control'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                raise forms.ValidationError('No existe un usuario con este correo electrónico.')
        return username

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'city', 'state', 'postal_code', 'country']
        
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email

class CustomPasswordChangeForm(PasswordChangeForm):
    pass

class CustomPasswordResetForm(PasswordResetForm):
    pass

class CustomSetPasswordForm(SetPasswordForm):
    pass