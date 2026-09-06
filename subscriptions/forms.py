from django import forms

from account.models import User


class ReporterSubscriberForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'full_name', 'email', 'mobile', 'city', 'district',
            'address', 'pincode', 'state', 'country',
        )
        labels = {'full_name': 'Full name', 'email': 'Email (optional)', 'pincode': 'PIN code'}
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.required = name != 'email'
            field.widget.attrs['class'] = 'form-control'

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']
        if User.objects.filter(mobile=mobile).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This mobile number is already registered.')
        return mobile

    def save(self, commit=True):
        subscriber = super().save(commit=False)
        parts = subscriber.full_name.split(' ', 1)
        subscriber.first_name = parts[0]
        subscriber.last_name = parts[1] if len(parts) > 1 else ''
        if commit:
            subscriber.save()
        return subscriber
