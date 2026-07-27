from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from .models import Profile, Address
    
class AddressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Si es una nueva dirección y el usuario ya tiene una dirección predeterminada,
        # desactivar la opción de establecer como predeterminada por defecto
        if self.instance.pk is None and self.user:
            if Address.objects.filter(user=self.user, is_default=True).exists():
                self.fields['is_default'].initial = False
            else:
                self.fields['is_default'].initial = True

    # Usar CharField en lugar de ChoiceField, ya que las opciones se manejan dinámicamente con JS
    department = forms.CharField(
        max_length=100,
        label='Departamento',
        widget=forms.Select(attrs={
            'id': 'department',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )
    province = forms.CharField(
        max_length=100,
        label='Provincia',
        widget=forms.Select(attrs={
            'id': 'province',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )
    district = forms.CharField(
        max_length=100,
        label='Distrito',
        widget=forms.Select(attrs={
            'id': 'district',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        })
    )
    street = forms.CharField(
        max_length=100, 
        label='Calle/Avenida', 
        widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500', 'placeholder': 'Nombre de la calle o avenida'})
    )
    street_number = forms.CharField(
        max_length=50, 
        label='Número/Lote/Dpto', 
        widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500', 'placeholder': 'Ej: 123, Lote 5, Dpto 101'})
    )
    additional_info = forms.CharField(
        required=False, 
        label='Información Adicional (Opcional)', 
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500', 'placeholder': 'Referencia, color de casa, etc.'})
    )
    is_default = forms.BooleanField(
        required=False,
        label='Establecer como dirección predeterminada',
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'})
    )
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = Address
        fields = [
            'department', 'province', 'district', 
            'street', 'street_number', 'additional_info', 
            'is_default', 'latitude', 'longitude'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get('department')
        province = cleaned_data.get('province')
        district = cleaned_data.get('district')

        if not department:
            self.add_error('department', 'Este campo es obligatorio.')
        if not province:
            self.add_error('province', 'Este campo es obligatorio.')
        if not district:
            self.add_error('district', 'Este campo es obligatorio.')

        return cleaned_data

    def save(self, commit=True):
        address = super().save(commit=False)
        address.department = self.cleaned_data.get('department')
        address.province = self.cleaned_data.get('province')
        address.district = self.cleaned_data.get('district')
        address.street = self.cleaned_data.get('street')
        address.street_number = self.cleaned_data.get('street_number')
        address.additional_info = self.cleaned_data.get('additional_info')
        address.is_default = self.cleaned_data.get('is_default')
        
        if commit:
            address.user = self.user  # Asegúrate de asignar el usuario
            address.save()
        return address
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    # Nuevos campos
    DOCUMENT_CHOICES = [
        ('DNI', 'DNI'),
        ('CE', 'Carnet de Extranjería'),
        ('Pasaporte', 'Pasaporte')
    ]
    document_type = forms.ChoiceField(choices=DOCUMENT_CHOICES, required=True)
    document_number = forms.CharField(max_length=20, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    
    # Campos para términos y condiciones
    accept_terms = forms.BooleanField(required=True)
    accept_privacy = forms.BooleanField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'document_type', 'document_number', 'phone_number', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email
        
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            profile, created = Profile.objects.get_or_create(user=user)
            profile.phone_number = self.cleaned_data.get('phone_number')
            profile.document_type = self.cleaned_data.get('document_type')
            profile.document_number = self.cleaned_data.get('document_number')
            profile.save()
        return user

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
        fields = ['phone_number', 'document_type', 'document_number']
        
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