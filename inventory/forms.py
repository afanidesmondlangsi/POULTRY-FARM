
from django import forms


class FeedTransactionForm(forms.Form):

    transaction_type = forms.ChoiceField(
        choices=[
            ("RECEIVED", "Feed Received"),
            ("USED", "Feed Used"),
        ],
        widget=forms.Select(
            attrs={"class": "form-select"}
        )
    )

    quantity = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        label="Number of Feed Bags",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01"
            }
        )
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2
            }
        )
    )
