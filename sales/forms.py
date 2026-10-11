
from django import forms
from .models import Sale


class SaleForm(forms.ModelForm):

    class Meta:
        model = Sale

        fields = [
            "product_type",
            "quantity",
            "unit_price",
            "trays_per_box",
        ]

        widgets = {
            "product_type": forms.Select(
                attrs={"class": "form-select"}
            ),

            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),

            "unit_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "0.01",
                }
            ),

            "trays_per_box": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "placeholder": "Required for box sales",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        product_type = cleaned_data.get("product_type")
        quantity = cleaned_data.get("quantity")
        unit_price = cleaned_data.get("unit_price")
        trays_per_box = cleaned_data.get("trays_per_box")

        if quantity is not None and quantity <= 0:
            self.add_error(
                "quantity",
                "Quantity must be greater than zero."
            )

        if unit_price is not None and unit_price < 0:
            self.add_error(
                "unit_price",
                "Selling price cannot be negative."
            )

        if product_type == "BOX":
            if trays_per_box is None or trays_per_box <= 0:
                self.add_error(
                    "trays_per_box",
                    "Enter the number of trays in each box."
                )
        elif trays_per_box is not None:
            self.add_error(
                "trays_per_box",
                "Only enter trays per box for box sales."
            )

        return cleaned_data

class SaleCorrectionForm(SaleForm):

    reason = forms.CharField(
        label="Reason for correction",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Explain why this sale is being corrected",
            }
        ),
        required=True,
        min_length=5,
    )

    class Meta(SaleForm.Meta):
        fields = [
            "product_type",
            "quantity",
            "unit_price",
            "trays_per_box",
        ]
