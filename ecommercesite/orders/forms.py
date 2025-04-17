from django import forms
from .models import Order
from .locations import PERU_LOCATIONS, get_provinces, get_districts, get_departments

class BaseLocationForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'department', 'province', 'district', 'city', 'address', 'street',
            'street_number', 'additional_info', 'recipient', 'postal_code', 'country'
        ]
        widgets = {
            'department': forms.Select(
                choices=[('', 'Seleccione un departamento')],
                attrs={'id': 'id_department', 'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}
            ),
            'province': forms.Select(
                choices=[('', 'Seleccione una provincia')],
                attrs={'id': 'id_province', 'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}
            ),
            'district': forms.Select(
                choices=[('', 'Seleccione un distrito')],
                attrs={'id': 'id_district', 'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}
            ),
            'city': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ciudad'}),
            'address': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'street': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'street_number': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'additional_info': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'recipient': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'postal_code': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'country': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        departments = get_departments()
        self.fields['department'].choices = [('', 'Seleccione un departamento')] + [(dept, dept) for dept in departments]

        if 'department' in self.data or self.initial.get('department'):
            try:
                department = self.data.get('department', self.initial.get('department'))
                provinces = get_provinces(department)
                self.fields['province'].choices = [('', 'Seleccione una provincia')] + [(prov, prov) for prov in provinces]
            except (ValueError, TypeError) as e:
                self.fields['province'].choices = [('', 'Seleccione una provincia')]

        if 'province' in self.data or self.initial.get('province'):
            try:
                department = self.data.get('department', self.initial.get('department'))
                province = self.data.get('province', self.initial.get('province'))
                districts = get_districts(department, province)
                self.fields['district'].choices = [('', 'Seleccione un distrito')] + [(dist, dist) for dist in districts]
            except (ValueError, TypeError) as e:
                self.fields['district'].choices = [('', 'Seleccione un distrito')]

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get('department')
        province = cleaned_data.get('province')
        district = cleaned_data.get('district')
        city = cleaned_data.get('city')
        street = cleaned_data.get('street')
        street_number = cleaned_data.get('street_number')
        recipient = cleaned_data.get('recipient')
        
        # Validar ubicaciones
        if department and department not in get_departments():
            self.add_error('department', 'Departamento no válido.')
        if department and province and province not in get_provinces(department):
            self.add_error('province', 'Provincia no válida para el departamento seleccionado.')
        if department and province and district and district not in get_districts(department, province):
            self.add_error('district', 'Distrito no válido para la provincia seleccionada.')
            
        # Validar campos obligatorios de dirección
        if not city:
            self.add_error('city', 'La ciudad es obligatoria.')
        if not street:
            self.add_error('street', 'La calle es obligatoria.')
        if not street_number:
            self.add_error('street_number', 'El número es obligatorio.')
        if not recipient:
            self.add_error('recipient', 'El destinatario es obligatorio.')
            
        return cleaned_data

# Resto de los formularios sin cambios
class OrderCreateForm(BaseLocationForm):
    terms_accepted = forms.BooleanField(
        label="Al confirmar tu compra, acepto los términos y condiciones y las Políticas de Privacidad",
        required=True
    )

    class Meta(BaseLocationForm.Meta):
        fields = BaseLocationForm.Meta.fields + [
            'first_name', 'last_name', 'email', 'phone', 'invoice_requested'
        ]
        widgets = BaseLocationForm.Meta.widgets | {
            'first_name': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'last_name': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'email': forms.EmailInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'phone': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'invoice_requested': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-blue-600 rounded border-gray-300'}),
        }

class OrderIdentificationForm(forms.ModelForm):
    terms_accepted = forms.BooleanField(
        label="Al confirmar tu compra, acepto los términos y condiciones y las Políticas de Privacidad",
        required=True
    )
    data_usage = forms.BooleanField(
        label="Autorizo el tratamiento de mis datos para fines adicionales.",
        required=False
    )
    invoice_requested = forms.BooleanField(
        label="DESEO FACTURA",
        required=False
    )
    document_type = forms.ChoiceField(
        label="Tipo de documento",
        choices=Order.DOCUMENT_TYPE_CHOICES,
        required=False
    )
    document_number = forms.CharField(
        label="Documento",
        max_length=20,
        required=False
    )

    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'invoice_requested',
            'document_type', 'document_number'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'first_name': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'last_name': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'phone': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'document_type': forms.Select(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'document_number': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document_type'].required = False
        self.fields['document_number'].required = False

class OrderShippingForm(BaseLocationForm):
    class Meta(BaseLocationForm.Meta):
        widgets = BaseLocationForm.Meta.widgets | {
            'address': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Dirección completa'}),
            'street': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Avenida Los Alisos'}),
            'street_number': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': '758'}),
            'additional_info': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Apto. 201'}),
            'recipient': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Nombre del destinatario'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].required = True
        self.fields['province'].required = True
        self.fields['district'].required = True
        self.fields['city'].required = True  # Hacer que el campo city sea obligatorio
        self.fields['street'].required = True
        self.fields['street_number'].required = True
        self.fields['recipient'].required = True