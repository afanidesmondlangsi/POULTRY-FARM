
from django import forms
from .models import Harvest


class HarvestForm(forms.ModelForm):
    class Meta:
        model = Harvest

        fields = [
            "shift",
            "trays_harvested",
            "half_trays_harvested",
            "boxes_harvested",
            "trays_per_box",
        ]

        widgets = {
            "shift": forms.Select(
                attrs={"class": "form-select"}
            ),
            "trays_harvested": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0
                }
            ),
            "boxes_harvested": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0
                }
            ),
        }

    
def clean(self):
    cleaned = super().clean()

    full_trays = cleaned.get("trays_harvested") or 0
    half_trays = cleaned.get("half_trays_harvested") or 0
    boxes = cleaned.get("boxes_harvested") or 0
    trays_per_box = cleaned.get("trays_per_box")

    if full_trays == 0 and half_trays == 0 and boxes == 0:
        raise forms.ValidationError(
            "Enter at least one harvested quantity."
        )

    if boxes > 0 and trays_per_box is not None:
        if trays_per_box < 1:
            self.add_error(
                "trays_per_box",
                "Trays per box must be greater than zero."
            )

    return cleaned

