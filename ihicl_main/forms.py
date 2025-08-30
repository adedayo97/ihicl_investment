# forms.py
from django import forms
from django.contrib.auth.models import User
from .models import InvestorProfile

from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
import re




class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)
    subject = forms.ChoiceField(
        choices=[
            ('General Inquiry', 'General Inquiry'),
            ('Investment Opportunities', 'Investment Opportunities'),
            ('Account Support', 'Account Support'),
            ('Partnership', 'Partnership'),
        ],
        required=True
    )
    message = forms.CharField(widget=forms.Textarea, required=True)
    
    # Add reCAPTCHA field
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)    
    

    #captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)


from django import forms

class LoginForm(forms.Form):
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput())



# forms.py - Update ProfileUpdateForm
class ProfileUpdateForm(forms.ModelForm):
    title = forms.ChoiceField(
        choices=InvestorProfile.TITLE_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    other_title = forms.CharField(
        max_length=50, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specify your title'})
    )
    email = forms.EmailField()
    telephone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)
    country = forms.CharField(max_length=100, required=False)
    city = forms.CharField(max_length=100, required=False)
    state = forms.CharField(max_length=100, required=False)
    postal_code = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
    
    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        if hasattr(self.instance, 'investor_profile'):
            investor_profile = self.instance.investor_profile
            self.fields['title'].initial = investor_profile.title
            self.fields['other_title'].initial = investor_profile.other_title
            self.fields['telephone'].initial = investor_profile.telephone
            self.fields['address'].initial = investor_profile.address
            self.fields['country'].initial = investor_profile.country
            self.fields['city'].initial = investor_profile.city
            self.fields['state'].initial = investor_profile.state
            self.fields['postal_code'].initial = investor_profile.postal_code
    
    def save(self, commit=True):
        user = super(ProfileUpdateForm, self).save(commit=False)
        if commit:
            user.save()
            investor_profile, created = InvestorProfile.objects.get_or_create(user=user)
            investor_profile.title = self.cleaned_data['title']
            investor_profile.other_title = self.cleaned_data['other_title']
            investor_profile.telephone = self.cleaned_data['telephone']
            investor_profile.address = self.cleaned_data['address']
            investor_profile.country = self.cleaned_data['country']
            investor_profile.city = self.cleaned_data['city']
            investor_profile.state = self.cleaned_data['state']
            investor_profile.postal_code = self.cleaned_data['postal_code']
            investor_profile.save()
        return user
    

class InvestmentForm(forms.Form):
    amount = forms.DecimalField(
        label="Investment Amount (₦)",
        min_value=10000,  # Minimum investment of ₦10,000
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'})
    )
    terms = forms.BooleanField(
        label="I agree to the terms and conditions",
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


# Add this to forms.py at the end

class WithdrawForm(forms.Form):
    amount = forms.DecimalField(
        label="Withdrawal Amount (₦)",
        min_value=1000,  # Minimum withdrawal of ₦1,000 - adjust as needed
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'})
    )
    terms = forms.BooleanField(
        label="I agree to the terms and conditions",
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class InvestmentRegistrationForm(UserCreationForm):
    title = forms.ChoiceField(
        choices=InvestorProfile.TITLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    other_title = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specify your title'})
    )
    telephone = forms.CharField(max_length=20, required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=True)
    country = forms.CharField(max_length=100, required=True)
    city = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)
    postal_code = forms.CharField(max_length=20, required=False)
    investment_amount = forms.DecimalField(
        min_value=10000,
        max_digits=12,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum ₦10,000'})
    )
    terms = forms.BooleanField(required=True)
    newsletter = forms.BooleanField(required=False)
    
    # Add reCAPTCHA field
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)
    
    class Meta:
        model = User
        fields = ['title', 'other_title', 'first_name', 'last_name', 'email', 
                 'telephone', 'address', 'country', 'city', 'state', 'postal_code',
                 'investment_amount', 'password1', 'password2', 'terms', 'newsletter']
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        
        # Password strength validation
        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password1):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password1):
            raise ValidationError("Password must contain at least one lowercase letter")
        
        if not re.search(r'[0-9]', password1):
            raise ValidationError("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
            raise ValidationError("Password must contain at least one special character")
        
        return password2
    
    def clean_investment_amount(self):
        amount = self.cleaned_data.get('investment_amount')
        if amount < 10000:
            raise ValidationError("Minimum investment amount is ₦10,000")
        return 
    

class StatementRequestForm(forms.Form):
    period_start = forms.DateField(
        label="Start Date",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    period_end = forms.DateField(
        label="End Date",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    notes = forms.CharField(
        label="Additional Notes",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any specific requirements for your statement...'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        period_start = cleaned_data.get('period_start')
        period_end = cleaned_data.get('period_end')
        
        if period_start and period_end and period_start > period_end:
            raise forms.ValidationError("Start date cannot be after end date.")
        
        return cleaned_data