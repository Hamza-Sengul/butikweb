from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'surname', 'email', 'content', 'rating']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adınızı giriniz'}),
            'surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soyadınızı giriniz'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email adresinizi giriniz'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Yorumunuzu yazınız', 'rows': 4, 'style': 'padding: 10px;'}),
            'rating': forms.HiddenInput(),  # Bu kısmı JavaScript ile işleteceğiz
        }
