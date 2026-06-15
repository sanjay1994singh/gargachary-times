from django import forms

from .models import Edition


class EditionUploadForm(forms.ModelForm):
    class Meta:
        model = Edition
        fields = ["city", "section", "publish_date", "pdf"]
        widgets = {
            "publish_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_pdf(self):
        pdf = self.cleaned_data["pdf"]
        if not pdf.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Please upload a PDF file.")
        return pdf
