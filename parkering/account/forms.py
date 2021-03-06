from django import forms
from account.models import User_data, Apartment_number
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib import auth
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.core.validators import RegexValidator

minimum_password_length = 8


# dynamic loginform
class LoginForm(forms.Form):
    # fields
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))

    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    # validation

    # if user and user is active
    def clean_password(self):
        cleaned_username = self.cleaned_data['username']
        cleaned_password = self.cleaned_data['password']

        user = auth.authenticate(username = cleaned_username, password = cleaned_password)

        if user is not None:
            if not user.is_active:
                raise forms.ValidationError(u"This account has been inactivated.")
        else:
            raise forms.ValidationError(u"Incorrect login, please try again or register an account.")

        return cleaned_password


# register form
class RegisterForm(forms.Form):
    
    # validators
    alphanumeric_validator = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only the letters A to Z and numbers are allowed.')
    phone_number_validator = RegexValidator(r'^(\+[0-9]{4}|0?[0-9]{3})(\ |\-)?([0-9]{1,2})(\ |\-)?([0-9]{1,2})(\ |\-)?([0-9]{1,3})$', 'The phone number entered is not valid.')
    
    # fields
    username = forms.CharField(min_length=3,validators=[alphanumeric_validator],widget=forms.TextInput(attrs={'placeholder': 'Username'}))

    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'First name'}))

    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Last name'}))

    email = forms.CharField(widget=forms.EmailInput(attrs={'placeholder': 'E-mail address'}))

    password = forms.CharField(min_length=minimum_password_length,widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    password_repeat = forms.CharField(min_length=minimum_password_length,widget=forms.PasswordInput(attrs={'placeholder': 'Repeat password'}))

    phone_number = forms.CharField(validators=[phone_number_validator],widget=forms.TextInput(attrs={'placeholder': 'Phone number'}))

    apartment = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Apartment number'}))
    
    # validation

    # if username already exists
    def clean_username(self):
        cleaned_username = self.cleaned_data['username']
        
        if User.objects.filter(username=cleaned_username).exists():
            raise forms.ValidationError(u"The username %s is already taken." % cleaned_username)
            
        return cleaned_username

    # if passwords do not match or password repeat missing
    def clean_password_repeat(self):
        #Check if the password was repeated, and if the repeated password is a match.
        cleaned_password = self.cleaned_data.get('password')
        cleaned_password_repeat = self.cleaned_data['password_repeat']

        if not cleaned_password_repeat:
            raise forms.ValidationError(u"Please repeat the password.")
        if cleaned_password != cleaned_password_repeat:
            raise forms.ValidationError(u"The passwords do not match.")
            
        return cleaned_password_repeat

    # if apartment number does not exist or is already in us
    def clean_apartment(self):
        cleaned_apartment = self.cleaned_data['apartment']
        
        if User_data.objects.filter(apartment=cleaned_apartment).exists():
            raise forms.ValidationError(u"This apartment number is already in use.")
            
        if not Apartment_number.objects.filter(apartment_number=cleaned_apartment).exists():
            raise forms.ValidationError(u"This apartment number does not exist.")
            
        return cleaned_apartment

    # check if email already exist
    def clean_email(self):
        cleaned_email = self.cleaned_data['email']

        # cast error if exists
        if User.objects.filter(email=cleaned_email).exists():
            raise forms.ValidationError(u"This email already belongs to another account.")

        return cleaned_email

# change password for logged in users
class ChangePassword(forms.Form):

    # fields
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Current password'}))
    
    password = forms.CharField(min_length=minimum_password_length,widget=forms.PasswordInput(attrs={'placeholder': 'New password'}))
        
    repeat_password = forms.CharField(min_length=minimum_password_length,widget=forms.PasswordInput(attrs={'placeholder': 'Repeat password'}))

    # init self
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(ChangePassword, self).__init__(*args, **kwargs)
    
    # validation

    # if incorrect password
    def clean_current_password(self):
        cleaned_username = self.user.username
        cleaned_password = self.cleaned_data['current_password']

        user = auth.authenticate(username = cleaned_username, password = cleaned_password)
        
        if user is None:
            raise forms.ValidationError(u"Incorrect password, please try again.")

        return cleaned_password

    # if passwords does not match or if repeat password is empty
    def clean_repeat_password(self):
        #Check if the password was repeated, and if the repeated password is a match.
        cleaned_password = self.cleaned_data.get('password')
        cleaned_repeat_password = self.cleaned_data['repeat_password']

        if not cleaned_repeat_password:
            raise forms.ValidationError(u"Please repeat the password.")
        if cleaned_password != cleaned_repeat_password:
            raise forms.ValidationError(u"The passwords do not match.")
            
        return cleaned_repeat_password

# change user information for logged in users
class ChangeDetails(forms.Form):
    
    # fields
    phone_number_validator = RegexValidator(r'^(\+[0-9]{4}|0?[0-9]{3})(\ |\-)?([0-9]{1,2})(\ |\-)?([0-9]{1,2})(\ |\-)?([0-9]{1,3})$', 'The phone number entered is not valid.')
    
    email = forms.CharField(widget=forms.EmailInput(attrs={'placeholder': 'E-mail address'}))
        
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Last name'}))
    
    phone_number = forms.CharField(validators=[phone_number_validator],widget=forms.TextInput(attrs={'placeholder': 'Phone number'}))

    # validation

    # extra validation through django native
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(ChangeDetails, self).__init__(*args, **kwargs)

        for key in self.fields:
            self.fields[key].required = False
            
        self.fields['email'].initial = self.user.email
        
        self.fields['first_name'].initial = self.user.first_name
        
        self.fields['last_name'].initial = self.user.last_name
        
        self.fields['phone_number'].initial = User_data.objects.get(user=self.user).phone_number

    # check if email already exist
    def clean_email(self):
        cleaned_email = self.cleaned_data['email']
        
        # cast error if email is in use of another account
        if cleaned_email != None and len(cleaned_email) > 0 and cleaned_email != self.user.email and User.objects.filter(email=cleaned_email).exists():
            raise forms.ValidationError(u"This email already belongs to another account.")

        return cleaned_email


# password reset form
class PasswordResetRequestForm(forms.Form):

    # fields
    email = forms.CharField(widget=forms.EmailInput(attrs={'placeholder': 'E-mail adress'}))

    # Validation

    # if email does not exist
    def clean_email(self):
        cleaned_email = self.cleaned_data['email']
        
        if not User.objects.filter(email=cleaned_email).exists():
            raise forms.ValidationError(u"No user related to this e-mail adress found.")
            
        return cleaned_email

# password change form
class PasswordChangeForm(forms.Form):

    # fields
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),min_length=minimum_password_length)
         
    password_repeat = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Repeat password'}),min_length=minimum_password_length)
    
    # init self
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
    
    # validation

    # if passwords do not match or if repeat password is empty
    def clean_password_repeat(self):
        #Check if the password was repeated, and if the repeated password is a match.
        cleaned_password = self.cleaned_data.get('password')
        cleaned_password_repeat = self.cleaned_data['password_repeat']

        if not cleaned_password_repeat:
            raise forms.ValidationError(u"Please repeat the password.")
        if cleaned_password != cleaned_password_repeat:
            raise forms.ValidationError(u"The passwords do not match.")
            
        return cleaned_password_repeat

    # save user password
    def save(self, commit=True):
        password = self.cleaned_data["password"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
