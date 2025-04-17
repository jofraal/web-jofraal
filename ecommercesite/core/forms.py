from django import forms
from .models import Reclamacion

class ReclamacionForm(forms.ModelForm):
    class Meta:
        model = Reclamacion
        exclude = ['fecha_hora', 'numero_correlativo', 'fecha_creacion', 'fecha_actualizacion', 'observaciones']
        labels = {
            'nombres': 'Nombres',
            'apellidos': 'Apellidos',
            'tipo_documento': 'Tipo de Documento',
            'numero_documento': 'Número de Documento',
            'departamento': 'Departamento',
            'provincia': 'Provincia',
            'distrito': 'Distrito',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'email': 'Correo Electrónico',
            'representante': 'Padre o Madre / Representante (en el caso que usted sea menor de edad)',
            'tipo_solicitud': 'Tipo de Solicitud',
            'numero_pedido': 'Número de Pedido',  # Cambiado de Nombre del Pedido a Número de Pedido
            'monto_reclamado': 'Monto Reclamado (S/)',
            'tipo_reclamo': 'Tipo de Reclamo',
            'detalle': 'Detalle de la Reclamación',
            'pedido': 'Pedido del Consumidor',
        }
        widgets = {
            'detalle': forms.Textarea(attrs={'rows': 6, 'maxlength': 1200}),
            'pedido': forms.Textarea(attrs={'rows': 4, 'maxlength': 300}),
            'tipo_solicitud': forms.RadioSelect(attrs={'class': 'h-4 w-4'}),
            'tipo_reclamo': forms.RadioSelect(attrs={'class': 'h-4 w-4'}),
            'tipo_documento': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Estilos base con Tailwind para todos los campos (excepto radio buttons)
        base_classes = 'w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500'

        # Personalizar widgets y añadir clases
        for field_name, field in self.fields.items():
            # Añadir clases de Tailwind solo a campos que no sean radio buttons
            if field_name not in ['tipo_solicitud', 'tipo_reclamo']:
                field.widget.attrs.update({'class': base_classes})

            # Marcar campos requeridos explícitamente
            if field.required:
                field.widget.attrs['required'] = 'required'
                field.label += ' *'  # Añadir asterisco visual a etiquetas requeridas

            # Personalizaciones específicas
            if field_name in ['detalle', 'pedido']:
                field.widget.attrs.update({'placeholder': f'Escribe aquí (máx. {field.widget.attrs["maxlength"]} caracteres)'})
            elif field_name == 'email':
                field.widget.attrs.update({'type': 'email', 'placeholder': 'ejemplo@correo.com'})
            elif field_name == 'telefono':
                field.widget.attrs.update({'type': 'tel', 'placeholder': 'Ej. 987654321'})
            elif field_name == 'monto_reclamado':
                field.widget.attrs.update({'step': '0.01', 'placeholder': 'Ej. 150.00'})
            elif field_name == 'numero_pedido':  # Cambiado de nombre_pedido a numero_pedido
                field.widget.attrs.update({'placeholder': 'Ej. 123456'})

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono and not telefono.isdigit():
            raise forms.ValidationError("El teléfono debe contener solo números.")
        if telefono and len(telefono) < 9:
            raise forms.ValidationError("El teléfono debe tener al menos 9 dígitos.")
        return telefono

    def clean_monto_reclamado(self):
        monto = self.cleaned_data.get('monto_reclamado')
        if monto <= 0:
            raise forms.ValidationError("El monto reclamado debe ser mayor que cero.")
        return monto