from django import forms
from .models import ProductReview

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f'{i} estrellas') for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'placeholder': 'Escribe un comentario (opcional)', 'rows': 3}),
        }
