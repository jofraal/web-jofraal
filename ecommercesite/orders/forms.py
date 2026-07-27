from django import forms
from .models import Order
import logging

logger = logging.getLogger(__name__)

class BaseLocationForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'department', 'province', 'district', 'city', 'address', 'street',
            'street_number', 'additional_info', 'country', 'latitude', 'longitude'
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
            'address': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Dirección completa'}),
            'street': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'street_number': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'additional_info': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'country': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .locations import get_departments, get_provinces, get_districts

        try:
            departments = get_departments()
            logger.info(f"Departamentos cargados: {departments}")
            self.fields['department'].choices = [('', 'Seleccione un departamento')] + [(dept, dept) for dept in departments]
        except Exception as e:
            logger.error(f"Error al cargar departamentos: {e}")
            self.fields['department'].choices = [('', 'Seleccione un departamento')]

        department = None
        if 'department' in self.data:
            department = self.data.get('department')
            logger.info(f"Departamento seleccionado desde POST: {department}")
        elif self.initial.get('department'):
            department = self.initial.get('department')
            logger.info(f"Departamento seleccionado desde initial: {department}")
        elif self.instance and self.instance.department:
            department = self.instance.department
            logger.info(f"Departamento seleccionado desde instancia: {department}")

        if department:
            try:
                provinces = get_provinces(department)
                logger.info(f"Provincias cargadas para {department}: {provinces}")
                self.fields['province'].choices = [('', 'Seleccione una provincia')] + [(prov, prov) for prov in provinces]
            except Exception as e:
                logger.error(f"Error al cargar provincias para {department}: {e}")
                self.fields['province'].choices = [('', 'Seleccione una provincia')]

        province = None
        if 'province' in self.data:
            province = self.data.get('province')
            logger.info(f"Provincia seleccionada desde POST: {province}")
        elif self.initial.get('province'):
            province = self.initial.get('province')
            logger.info(f"Provincia seleccionada desde initial: {province}")
        elif self.instance and self.instance.province:
            province = self.instance.province
            logger.info(f"Provincia seleccionada desde instancia: {province}")

        if department and province:
            try:
                districts_data = get_districts(department, province)
                districts = [dist.strip() for dist in districts_data] if isinstance(districts_data, list) else []
                logger.info(f"Distritos cargados para {province}: {districts}")
                self.fields['district'].choices = [('', 'Seleccione un distrito')] + [(dist, dist) for dist in districts]
                self.fields['district'].widget.attrs['disabled'] = False
            except Exception as e:
                logger.error(f"Error al cargar distritos para {department}, {province}: {e}")
                self.fields['district'].choices = [('', 'Seleccione un distrito')]

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get('department')
        province = cleaned_data.get('province')
        district = cleaned_data.get('district')
        city = cleaned_data.get('city')
        street = cleaned_data.get('street')
        street_number = cleaned_data.get('street_number')
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        address = cleaned_data.get('address')

        from .locations import get_departments, get_provinces, get_districts

        # Validar que address no sea "Pendiente"
        if address and address.lower() == 'pendiente':
            self.add_error('address', 'La dirección no puede ser "Pendiente".')

        if department and department not in get_departments():
            self.add_error('department', 'Departamento no válido.')
        if department and province and province not in get_provinces(department):
            self.add_error('province', 'Provincia no válida para el departamento seleccionado.')
        if department and province and district:
            districts_data = get_districts(department, province)
            districts = [dist.strip() for dist in districts_data] if isinstance(districts_data, list) else []
            logger.info(f"Distritos recargados en clean para {province}: {districts}")
            if district not in districts:
                self.add_error('district', 'Distrito no válido para la provincia seleccionada.')
            else:
                self.fields['district'].choices = [('', 'Seleccione un distrito')] + [(dist, dist) for dist in districts]

        if not city:
            self.add_error('city', 'La ciudad es obligatoria.')
        if not street:
            self.add_error('street', 'La calle es obligatoria.')
        if not street_number:
            self.add_error('street_number', 'El número es obligatorio.')

        if latitude is None or longitude is None or latitude == '' or longitude == '':
            self.add_error('latitude', 'La latitud es obligatoria.')
            self.add_error('longitude', 'La longitud es obligatoria.')
        else:
            try:
                lat = float(latitude)
                lng = float(longitude)
                if not (-90 <= lat <= 90):
                    self.add_error('latitude', 'La latitud debe estar entre -90 y 90.')
                if not (-180 <= lng <= 180):
                    self.add_error('longitude', 'La longitud debe estar entre -180 y 180.')
            except Exception:
                self.add_error('latitude', 'La latitud debe ser un número válido.')
                self.add_error('longitude', 'La longitud debe ser un número válido.')

        return cleaned_data

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
        required=True
    )
    document_number = forms.CharField(
        label="Documento",
        max_length=20,
        required=True
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
        self.fields['document_type'].required = True
        self.fields['document_number'].required = True

class OrderShippingForm(BaseLocationForm):
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput())
    
    class Meta(BaseLocationForm.Meta):
        widgets = BaseLocationForm.Meta.widgets | {
            'address': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Dirección completa'}),
            'street': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Avenida Los Alisos'}),
            'street_number': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': '758'}),
            'additional_info': forms.TextInput(attrs={'class': 'px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Apto. 201'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].required = True
        self.fields['province'].required = True
        self.fields['district'].required = True
        self.fields['city'].required = True
        self.fields['street'].required = True
        self.fields['street_number'].required = True