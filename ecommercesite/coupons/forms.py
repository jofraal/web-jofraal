from django import forms

class CouponApplyForm(forms.Form):
    code = forms.CharField(label='Código de Cupón', widget=forms.TextInput(attrs={'class': 'border p-2 rounded w-full'}))