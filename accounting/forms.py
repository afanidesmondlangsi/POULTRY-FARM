
from django import forms
from django.utils import timezone

from .models import Expense


class ExpenseForm(forms.ModelForm):

    class Meta:
        model = Expense

        fields = [
            "business_date",
            "category",
            "description",
            "amount",
        ]

        widgets = {
            "business_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                },
                format="%Y-%m-%d",
            ),
            "category": forms.Select(
                attrs={"class": "form-select"}
            ),
            "description": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["business_date"].initial = (
            timezone.localdate()
        )
