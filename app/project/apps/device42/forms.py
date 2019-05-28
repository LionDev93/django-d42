from django.forms import Form, ModelForm, TextInput, PasswordInput, Select, Textarea, CheckboxInput, ValidationError, RadioSelect
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.urls import reverse_lazy
from django.conf import settings

from project.apps.device42 import models
from project.apps.device42.incognitos import INCOGNITO_LIST

class _BaseFormRecaptcha(object):
  """ Forms extending this class will validate reCaptcha element on clean """
  def __init__(self, *args, **kwargs):
    self.request = kwargs.pop('request', None)
    super(_BaseFormRecaptcha, self).__init__(*args, **kwargs)

  def clean(self):
    import urllib, urllib2, json
    super(_BaseFormRecaptcha, self).clean()
    url = settings.GOOGLE_RECAPTCHA_URL
    values = {
      'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
      'response': self.request.POST.get('g-recaptcha-response', None),
      'remoteip': self.request.META.get('REMOTE_ADDR', None),
    }

    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    result = json.loads(response.read())

    if not result["success"]:
      raise ValidationError(_('Only humans are allowed to submit this form.'))
    return self.cleaned_data

class _BaseFormIncognito(object):
  """Forms extending this class will verify field 'email' against INCOGNITOS list on clean"""
  def clean_email(self):
    email = self.cleaned_data.get('email', None)
    if (email is not None) and (email.split('@')[1] in INCOGNITO_LIST):
      raise ValidationError(_('Please use a valid work email address.'))
    elif email is None:
      raise ValidationError(_('Please use a valid work email address.'))
    return email

class DownloadForm(_BaseFormIncognito, ModelForm):
  field_order = ['instance_type', 'name', 'email', 'phone', 'cloud_password']
  def __init__(self, *args, **kwargs):
      super(DownloadForm, self).__init__(*args, **kwargs)
      self.fields['phone'].required = False
      self.fields['cloud_password'].required = False
      self.fields['I_agree_to_EULA'].label = mark_safe(_('I agree to <a target="_blank" href="%s">EULA</a> and <a target="_blank" href="%s">Privacy Policy</a>' %
                                                            (reverse_lazy('legal_eula'), reverse_lazy('legal_privacy'))))

  class Meta:
    model = models.AbstractDownloadForm
    fields = ('name', 'email', 'instance_type', 'phone', 'cloud_password', 'I_agree_to_EULA',)
    widgets = {
      'name': TextInput(attrs={'placeholder': _('Name'), 'required': 'required'}),
      'email': TextInput(attrs={'placeholder': _('Email Address'), 'required': 'required'}),
      'phone': TextInput(attrs={'placeholder': _('Phone')}),
      'cloud_password': PasswordInput(attrs={'placeholder': _('Cloud Password')}),
      'I_agree_to_EULA': CheckboxInput(attrs={'required':'required', 'class': 'form-checkbox'}),
    }

class OtherDownloadsForm(_BaseFormIncognito, ModelForm):
  class Meta:
    model = models.OtherDownloads
    fields = ('name', 'email',)
    widgets = {
      'name': TextInput(attrs={'placeholder': _('Name'), 'required': 'required'}),
      'email': TextInput(attrs={'placeholder': _('Email Address'), 'required': 'required'}),
    }

class TryDownloadsForm(_BaseFormIncognito, ModelForm):
  class Meta:
    model = models.AbstractDownloadForm
    fields = ('name', 'email',)
    widgets = {
      'name': TextInput(attrs={'placeholder': _('Full Name'), 'required': 'required'}),
      'email': TextInput(attrs={'placeholder': _('Work Email'), 'required': 'required'}),
    }

class ContactForm(_BaseFormRecaptcha, ModelForm):
  def __init__(self, *args, **kwargs):
    super(ContactForm, self).__init__(*args, **kwargs)
    self.fields['I_agree_to_EULA'].label = mark_safe(_('I agree to <a target="_blank" href="%s">Privacy Policy</a>' % reverse_lazy('legal_privacy')))

  class Meta:
    model = models.ContactModel
    fields = ('name', 'email', 'phone', 'topic', 'message', 'I_agree_to_EULA',)

    widgets = {
      'name': TextInput(attrs={'placeholder': _('Name')}),
      'email': TextInput(attrs={'placeholder': _('Email Address'), 'required': 'required'}),
      'phone': TextInput(attrs={'type': 'tel', 'placeholder': _('Phone Number')}),
      'message': Textarea(attrs={'placeholder': _('Please enter your message here'), 'class': 'form-control', 'required': 'required'}),
      'I_agree_to_EULA': CheckboxInput(attrs={'required':'required', 'class': 'form-checkbox'}),
    }

class ScheduleForm(_BaseFormIncognito, ModelForm):
  def __init__(self, *args, **kwargs):
    super(ScheduleForm, self).__init__(*args, **kwargs)
    self.fields['I_agree_to_EULA'].label = mark_safe(_('I agree to <a target="_blank" href="%s">Privacy Policy</a>' % reverse_lazy('legal_privacy')))

  class Meta:
    model = models.ScheduleModel
    fields = ('name', 'email', 'phone', 'I_agree_to_EULA',)
    widgets = {
      'phone': TextInput(attrs={'type': 'tel', 'placeholder': _('Phone Number'), 'class': 'form-control'}),
      'name': TextInput(attrs={'placeholder': _('Name'), 'class': 'form-control', 'required': 'required'}),
      'email': TextInput(attrs={'placeholder': _('Email Address'), 'class': 'form-control', 'required': 'required'}),
      'I_agree_to_EULA': CheckboxInput(attrs={'required':'required', 'class': 'form-checkbox'}),
    }

class PricingContactForm(ModelForm):
  DEVICE_COUNTS = (
    ('unknown', _('I am not sure'), '--'),
    ('100', '1 - 100 Devices', '1 - 1,000'),
    ('500', '101 - 500 Devices', '1,001 - 5,000'),
    ('1000', '501 - 1,000 Devices', '5,001 - 10K'),
    ('2500', '1,001 - 2,500 Devices', '10,001 - 25K'),
    ('5000', '2,501 - 5,000 Devices', '25,001 - 50K'),
    ('10000', '5,001 - 10K Devices', '50,001 - 100K'),
    ('25000', '10K - 25K', '100,001 - 250K'),
    ('25000plus', '25,001+ Devices', '250K+'),
  )

  def __init__(self, *args, **kwargs):
    super(PricingContactForm, self).__init__(*args, **kwargs)
    self.fields['I_agree_to_EULA'].label = mark_safe(_('I agree to <a target="_blank" href="%s">Privacy Policy</a>' % reverse_lazy('legal_privacy')))

  class Meta:
    model = models.PricingContactModel
    fields = ('name', 'email', 'company', 'phone', 'device_count', 'slm_addon', 'application_mapping_addon',
              'power_monitoring_addon', 'power_control_addon', 'referred_by_reseller', 'reseller_name', 'I_agree_to_EULA',)

    widgets ={
      'I_agree_to_EULA': CheckboxInput(attrs={'required':'required', 'class': 'form-checkbox'}),
    }

class FreeClientForm(_BaseFormIncognito, ModelForm):
  class Meta:
    model = models.FreeClient
    fields = ('email', 'Subscribe', 'I_agree_to_EULA')

    widgets ={
      'email': TextInput(attrs={'placeholder': _('Email Address'), 'required': 'required'}),
      'I_agree_to_EULA': CheckboxInput(attrs={'required':'required'}),
    }

class UpdateForm(_BaseFormIncognito, ModelForm):
  class Meta:
    model = models.UpdateModel
    fields = ('email',)

    widgets = {
      'email': TextInput(attrs={'placeholder': _('Email Address'), 'required': 'required'}),
    }

class BetaSignUpForm(ModelForm):
  class Meta:
    model = models.BetaSignUp
    fields = ('name', 'email',)
    widgets = {
      'name': TextInput(attrs={'placeholder': _('Name'), 'required':'required'}),
      'email': TextInput(attrs={'placeholder': _('Email'), 'required': 'required'}),
    }

class WebinarRegistrationForm(ModelForm):
  class Meta:
    model = models.OtherDownloads
    fields = ('first_name', 'last_name', 'email', 'title',)

    widgets = {
      'first_name': TextInput(attrs={'placeholder': _('First Name (Given name)')}),
      'last_name': TextInput(attrs={'placeholder': _('Last Name (Surname)')}),
      'email': TextInput(attrs={'placeholder': _('Work Email*'), 'type': 'email', 'required': 'required'}),
      'title': TextInput(attrs={'placeholder': _('Job Title')}),
    }

class SecondWebinarRegistrationForm(ModelForm):
  class Meta:
    model = models.OtherDownloads
    fields = ('email',)

    widgets = {
      'email': TextInput(attrs={'placeholder': _('Work Email*'), 'type': 'email', 'required': 'required'}),
    }

class Webinar2RegistrationForm(ModelForm):
  class Meta:
    model = models.OtherDownloads
    fields = ('first_name', 'last_name', 'email', 'title',)

    widgets = {
      'first_name': TextInput(attrs={'placeholder': _('First Name (Given name)')}),
      'last_name': TextInput(attrs={'placeholder': _('Last Name (Surname)')}),
      'email': TextInput(attrs={'placeholder': _('Work Email*'), 'type': 'email', 'required': 'required'}),
      'title': TextInput(attrs={'placeholder': _('Job Title')}),
    }

class LandingDownloadForm(_BaseFormIncognito, ModelForm):
  field_order = ['name', 'email', 'instance_type', 'cloud_password']
  def __init__(self, *args, **kwargs):
    super(LandingDownloadForm, self).__init__(*args, **kwargs)
    self.fields['cloud_password'].required = False

  class Meta:
    model = models.AbstractDownloadForm
    fields = ('name', 'email', 'instance_type', 'cloud_password')
    widgets = {
      'name': TextInput(attrs={'placeholder': _('Name'), 'required': 'required', 'class': 'form-control'}),
      'email': TextInput(attrs={'placeholder': _('Email Address'), 'required': 'required', 'class': 'form-control'}),
      'instance_type': RadioSelect(),
      'cloud_password': PasswordInput(attrs={'class': 'form-control'})
    }
    labels = {
      'name': _('Name'),
      'email': _('Email'),
      'instance_type': _('What version?'),
    }
