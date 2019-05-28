#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests, pytz, uuid, time, json, boto.ec2, boto.ec2.networkinterface
import threading
from datetime import datetime
from project.apps.device42.dme2 import DME2
from django import forms as forms
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render, redirect, resolve_url
from django.template import Context
from django.views.decorators.cache import never_cache, cache_page
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, get_language
from django.views.i18n import javascript_catalog
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST
from rest_framework.views import View
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from project.apps.device42 import models, view_logic, forms
from project.apps.device42.ots import OneTimeSecret
from project.apps.device42.incognitos import INCOGNITO_LIST
from project.apps.device42.landings import LANDING_DATA
from project.apps.upload.forms import UploadForm
from project.apps.upload.handler import UploadHandler
from project.apps.upload.slack import SlackNotifier


class DirectTemplateView(TemplateView):
  extra_context = None

  def get_context_data(self, **kwargs):
    context = super(self.__class__, self).get_context_data(**kwargs)
    if self.extra_context is not None:
      for key, value in self.extra_context.items():
        if callable(value):
          context[key] = value()
        else:
          context[key] = value
    return context


@cache_page(86400, key_prefix='js18n')
def cached_javascript_catalog(request, domain='djangojs', packages=None):
  from django.views.i18n import javascript_catalog
  return javascript_catalog(request, domain, packages)


def home(request):
  import feedparser

  BLOG_FEED = feedparser.parse('http://www.device42.com/blog/feed')
  LOGOS = _getClientLogos
  return render(request, 'home.html', {"logos": LOGOS, "blog_feed": BLOG_FEED, "is_home": True,})


@never_cache
def thanks(request, id=9):
  if not id or id is 9:
    return home(request)
  if 'temp_data' in request.session:
    return render(request, 'forms/thank-you.html', {'id': id, 'the_data': request.session['temp_data']})
  else:
    return render(request, 'forms/thank-you.html', {'id': id, 'the_data': None})


def faq_sales(request):
  return render(request, 'sections/product/faq_sales.html')


def faq_power(request):
  return render(request, 'sections/product/faq_power.html')


@never_cache
def schedule_form(request):
  the_ref = request.META.get('HTTP_REFERER', None)
  if request.method == 'POST':
    if request.POST['main'] == '':
      form = forms.ScheduleForm(request.POST)
      if form.is_valid():
        fc = form.save(commit=False)
        the_cookie = request.COOKIES.get('hubspotutk', None)
        fc.clicky_cookie = request.COOKIES.get('_jsuid', '')
        fc.intercom_id = request.COOKIES.get('intercom-id', '')
        fc.ip_address = client_address = request.META.get('REMOTE_ADDR', '')
        fc.request_cookies = request.COOKIES
        fc.save()

        name = form.cleaned_data['name']
        phone = form.cleaned_data['phone']
        sender = form.cleaned_data['email']

        message2 = """
        Name: %s
        Email: %s
        Phone: %s
        IP: %s
        """ % (name, sender, phone, client_address)
        from_address = ['support@device42.com']
        recipients = ['scanelli@device42.com', 'al.rossini@device42.com', ]  # 'raj@rajlog.com',
        if settings.DEBUG:
          recipients = ['dave.amato@device42.com', ]
        subject = "FYI: online demo - already sent an invite "

        send_mail(subject, message2, from_address, recipients)
        if not settings.DEBUG:
          view_logic.immediate_schedule_demo_send(name, sender)
          view_logic.hubspot_data_send('schedule_demo', the_cookie, client_address, the_ref, form.cleaned_data['name'],
                                       form.cleaned_data['email'], None, None, None, form.cleaned_data['phone'])

        request.session['temp_data'] = form.cleaned_data
        return redirect('thanks', id=0)
    else:
      if settings.DEBUG:
        send_to = ['dave.amato@device42.com', ]
      else:
        send_to = ['raj@rajlog.com', ]
      send_mail('demo -ve', str(request.POST), 'support@device42.com', send_to)
      return redirect('thanks', id=9)
  else:
    form_name = request.session.get('download_name', '')
    form_email = request.session.get('download_email', '')

    if form_name and form_email:
      form = forms.ScheduleForm({'name': form_name, 'email': form_email})
    else:
      form = forms.ScheduleForm()

  render_template = 'forms/schedule_demo.html'

  return render(request, render_template, {'form': form})


def customers(request):
  CLIENT_LOGOS = _getClientLogos()
  return render(request, 'sections/customers/_index.html', {'logos': CLIENT_LOGOS, })


def customers_testimonials(request):
  return render(request, 'sections/customers/testimonials.html')


def customers_social_mentions(request):
  return render(request, 'sections/customers/social-mentions.html')


def customers_case_studies(request):
  return render(request, 'sections/customers/case-studies.html')


def case_studies_intl_financial_service_provider(request):
  return render(request, 'sections/customers/_intl-financial-service-provider.html')


def case_studies_coventry_university(request):
  return render(request, 'sections/customers/_coventry-university.html')


def case_studies_maxihost(request):
  return render(request, 'sections/customers/_maxihost-data-center.html')


def case_studies_appdirect(request):
  return render(request, 'sections/customers/_appdirect.html')

def case_studies_gravity_rd(request):
  return render(request, 'sections/customers/_gravity.html')

def case_studies_netcetera_group(request):
  return render(request, 'sections/customers/_netcetera-group.html')

def case_studies_dell_emc(request):
  return render(request, 'sections/customers/_dell_emc.html')

def largest_virt_company(request):
  return render(request, 'sections/customers/_largest_virt_company.html')

def legal_d42_open_disc_eula(request):
  return render(request, 'sections/legal/d42_open_disc_eula.html')


def legal_eula(request):
  return render(request, 'sections/legal/eula.html')


def legal_privacy(request):
  return render(request, 'sections/legal/privacy.html')


def product(request):
  return redirect('/')


def product_benefits(request):
  return render(request, 'sections/product/benefits.html')


def use_cases(request):
  return render(request, 'sections/product/_use-cases.html')


def use_cases_budgeting_and_finance(request):
  return render(request, 'sections/product/use-cases/budgeting-and-finance.html')


def use_cases_capacity_planning(request):
  return render(request, 'sections/product/use-cases/capacity-planning.html')


def use_cases_data_center_and_cloud_migration(request):
  return render(request, 'sections/product/use-cases/data-center-and-cloud-migration.html')


def use_cases_hardware_audit(request):
  return render(request, 'sections/product/use-cases/hardware-audit.html')


def use_cases_it_agility(request):
  return render(request, 'sections/product/use-cases/it-agility.html')


def use_cases_it_automation(request):
  return render(request, 'sections/product/use-cases/it-automation.html')


def use_cases_mergers_and_acquisitions(request):
  return render(request, 'sections/product/use-cases/mergers-and-acquisitions.html')


def use_cases_migrations(request):
  return render(request, 'sections/product/use-cases/migrations.html')


def use_cases_software_audit_and_compliance(request):
  return render(request, 'sections/product/use-cases/software-audit-and-compliance.html')


def use_cases_security_and_compliance(request):
  return render(request, 'sections/product/use-cases/security-and-compliance.html')

def use_cases_change_management(request):
  return render(request, 'sections/product/use-cases/change-management.html')


@never_cache
def product_pricing(request):
  client_address = ''
  bot = False
  show_price = True
  if 'HTTP_USER_AGENT' in request.META:
    is_it_bot = view_logic.parse_user_agent(request.META.get('HTTP_USER_AGENT'))
    bot = True
    if not is_it_bot:
      if 'REMOTE_ADDR' in request.META:
        client_address = request.META['REMOTE_ADDR']
  if client_address:
    if 'ip' in request.GET:
      client_address = request.GET['ip']
    continent, country = view_logic.get_ip_data(client_address)
    country = str(country)
    if country in ['IN', 'AE', 'SA', 'OM', 'KW', 'QA', 'BH', 'IL', 'KR', 'MY', 'SG', 'TH', 'ID', 'VN', 'LA', 'PH']:
      show_price = False
  else:
    if not bot:
      boyd = 'no client ip found, here is meta ' + str(request.META)
      send_mail('pricing page no ip', boyd, 'support@device42.com', ['raj@rajlog.com', ])
  if show_price:
    return render(request, 'sections/product/pricing.html')
  else:
    # form processing code goes here
    if request.method == 'POST':  # If the form has been submitted...
      form = forms.PricingContactForm(request.POST)  # A form bound to the POST data
      if form.is_valid():  # All validation rules pass
        # Process the data in form.cleaned_data
        # ...
        fc = form.save(commit=False)
        if 'HTTP_REFERER' in request.META:
          the_ref = request.META['HTTP_REFERER']
        else:
          the_ref = None
        if 'hubspotutk' in request.COOKIES:
          the_cookie = request.COOKIES['hubspotutk']
        else:
          the_cookie = None
        fc.ip_address = client_address
        fc.country = country
        fc.save()
        message2 = json.dumps(form.cleaned_data, indent=2)
        from_address = 'support@device42.com'
        recipients = ['raj@rajlog.com', 'sales@device42.com']  # 'scanelli@device42.com']
        subject = 'Pricing Page Form'
        now = datetime.now()
        if settings.DEBUG:
          subject = '[testing] Pricing Page Form'
          recipients = ['raj@rajlog.com']
        if request.POST['address'] == '':

          html_body = '<html><head></head><body>' \
                       '<table width="500" cellpadding="3px" cellspacing="0" align="center">'
          text_body = ''
          for key in form.cleaned_data:

            html_body += '<tr><td style="border:1px solid #444444;padding:3px;" width="245"><b>' + \
                         key + '</b></td><td style="border:1px solid #444444;padding:3px;" width="245">'
            text_body += key + ': '
            if form.fields[key].__class__.__name__ == 'BooleanField':
              if form.cleaned_data.get(key):
                html_body += 'Yes'
                text_body += 'Yes'
              else:
                html_body += 'No'
                text_body += 'No'
            elif key == 'device_count':
              html_body += request.POST.get('device_count', '--').encode('utf-8')
              text_body += request.POST.get('device_count', '--').encode('utf-8')
            else:
              html_body += form.cleaned_data.get(key).encode('utf-8')
              text_body += form.cleaned_data.get(key).encode('utf-8')
            html_body += '</td></tr>'
            text_body += ' \n'

          html_body += '<tr><td style="border:1px solid #444444;padding:3px;" width="245"><b>Country</b></td><td style="border:1px solid #444444;padding:3px;" width="245">'
          html_body += country
          html_body += '<tr><td style="border:1px solid #444444;padding:3px;" width="245"><b>Submission Time</b></td><td style="border:1px solid #444444;padding:3px;" width="245">'
          html_body += now.strftime("%m-%d-%Y %I:%M%p")
          html_body += '</td></tr>'
          html_body += '<tr><td style="border:1px solid #444444;padding:3px;" width="245"><b>Language</b></td><td style="border:1px solid #444444;padding:3px;" width="245">'
          html_body += get_language()
          html_body += '</td></tr>'
          html_body += '<tr><td style="border:1px solid #444444;padding:3px;" width="245"><b>IP</b></td><td style="border:1px solid #444444;padding:3px;" width="245">'
          html_body += client_address
          html_body += '</td></tr></table></body></html>'

          text_body += 'Country: '
          text_body += country
          text_body += ' \n'
          text_body += 'Submission Time: '
          text_body += now.strftime("%m-%d-%Y %I:%M%p")
          text_body += ' \n'
          text_body += 'Language: '
          text_body += get_language()
          text_body += ' \n'
          text_body += 'IP: '
          text_body += client_address

          send_mail(subject, text_body, from_address, recipients, html_message=html_body)
        else:
          send_mail('pricing -ve', message2, from_address, ['raj@rajlog.com'])
        request.session['temp_data'] = form.cleaned_data
        return redirect('thanks', id=9)
    else:
      form = forms.PricingContactForm()  # An unbound form
    return render(request, "sections/product/nopricing.html", {'form': form})


def features(request):
  return render(request, 'sections/features/_features.html')


def features_dcim(request):
  return render(request, 'sections/features/data-center-management.html')


def features_itam(request):
  return render(request, 'sections/features/it-asset-management.html')


def features_ipam(request):
  return render(request, 'sections/features/ip-address-management.html')


def features_discovery(request):
  return render(request, 'sections/features/device-discovery.html')


def features_role_based_access(request):
  return render(request, 'sections/features/role-based-access.html')


def features_app_mapping(request):
  return render(request, 'sections/features/application-mapping.html')


def features_software_license(request):
  return render(request, 'sections/features/software-license-management.html')


def features_password_management(request):
  return render(request, 'sections/features/password-management.html')


def features_cloud_recommendation(request):
  return render(request, 'sections/features/cloud-recommendation.html')

def features_affinity_groups(request):
  return render(request, 'sections/features/affinity-groups.html')


def features_cmdb_for_cloud_era(request):
  return render(request, 'sections/features/cmdb-for-cloud-era.html')


def features_integrations(request):
  return render(request, 'sections/features/integrations.html')


def company(request):
  return render(request, 'sections/company/_company.html', {'include_company_info': True})


def company_about(request):
  return company(request)


def company_jobs(request):
  return render(request, 'sections/company/jobs.html', {'jobs': _getJobs()})


def company_jobs_devops(request):
  return render(request, 'sections/company/jobs_devops.html', {'jobs': _getJobs()})


def company_contact(request):
  form = forms.ContactForm()
  if request.method == 'POST':
    form = forms.ContactForm(request.POST, request=request)
    if form.is_valid():
      fc = form.save(commit=False)
      client_address = clicky_cookie = ''
      if 'HTTP_REFERER' in request.META:
        the_ref = request.META['HTTP_REFERER']
      else:
        the_ref = None
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if 'hubspotutk' in request.COOKIES:
        the_cookie = request.COOKIES['hubspotutk']
      else:
        the_cookie = None
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']

      fc.request_cookies = request.COOKIES
      fc.ip_address = client_address
      fc.clicky_cookie = clicky_cookie

      name = form.cleaned_data['name']
      subject = form.cleaned_data['topic']
      message = form.cleaned_data['message']
      sender = form.cleaned_data['email']
      phone = form.cleaned_data['phone']

      message2 = """
Contact Form Submission

Name: %s
Sender: %s
Phone: %s
Topic: %s
Message: %s
IP: %s
""" % (name, sender, phone, subject, message, client_address)
      from_address = 'support@device42.com'
      recipients = ['raj@rajlog.com', 'scanelli@device42.com', 'info@device42.com']
      if settings.DEBUG:
        recipients = [str(email) for i, email in settings.ADMINS]
      if request.POST['address'] == '':
        fc.save()
        send_mail('Contact Form', message2, from_address, recipients)
        view_logic.hubspot_data_send('contact', the_cookie, client_address, the_ref, form.cleaned_data['name'],
                                     form.cleaned_data['email'], form.cleaned_data['topic'],
                                     form.cleaned_data['message'],
                                     form.cleaned_data['phone'], form.cleaned_data['phone'])
      else:
        send_mail('contact -ve', message2, from_address, ['raj@rajlog.com',])
      request.session['temp_data'] = form.cleaned_data
      return redirect('thanks', id=6)
    else:
      pass
  return render(request, 'sections/company/contact.html', {'form': form})


@never_cache
@ensure_csrf_cookie
def upload(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        status_code = 200
        if form.is_valid():
            try:
                handler = UploadHandler(request, SlackNotifier())
                upload = handler.do_upload()
                response_content = {'success': True, 'upload': upload}
            except Exception, ex:
                response_content = {'failure': True, 'error': str(ex)}
                status_code = 500
        else:
            response_content = {'failure': True, 'error': 'invalid form'}
            status_code = 400
        return HttpResponse(content=json.dumps(response_content), status=status_code)
    else:
        return render(request, 'forms/upload.html')


@never_cache
def download(request):
  the_matrix = {'name': '',
                'email': '',
                'vp': '',
                'eula': False,
                'name_error': False,
                'email_error': False,
                'platform_error': False,
                'eula_error': False,
                'errors': False,
                }

  if request.method == 'POST':
    the_ref = client_address = clicky_cookie = intercom_id = the_cookie = request_cookies = ''
    if 'HTTP_REFERER' in request.META:
      the_ref = request.META['HTTP_REFERER']
    else:
      the_ref = None
    if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
    if 'hubspotutk' in request.COOKIES: the_cookie = request.COOKIES['hubspotutk']
    if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
    if 'intercom-id' in request.COOKIES:
      intercom_id = request.COOKIES['intercom-id']
    request_cookies = request.COOKIES

  if request.method == 'POST' and request.POST['instance_type'] == 'On-prem':
    if request.POST['main'] == '':
      form = forms.DownloadForm(request.POST)
      if form.is_valid():
        download_uuid = str(uuid.uuid1())
        email_clean = form.cleaned_data['email']
        name_clean = form.cleaned_data['name']
        dwnld = models.DownloadModel.objects.create(
          name=name_clean,
          email=email_clean,
          I_agree_to_EULA=True,
          ip_address=client_address,
          download_uuid=download_uuid,
          clicky_cookie=clicky_cookie,
          request_cookies=request_cookies
        )
        subject = 'Download'
        message2 = """
        Download Form Submission

        Name: %s
        Sender: %s
        Client IP: %s
        """ % (name_clean, email_clean, client_address)

        from_address = 'support@device42.com'
        recipients = ['raj@rajlog.com']
        if settings.DEBUG:
          recipients = ['dave.amato@device42.com', ]
        view_logic.immediate_download_send(request, name_clean, email_clean, download_uuid)
        send_mail(subject, message2, from_address, recipients)
        view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean,
                                     email_clean, '')
        request.session['temp_data'] = form.cleaned_data

      else:
        return render(request, 'forms/download.html', {'form': form})
    else:
      send_mail('download -ve', str(request.POST), 'support@device42.com', ['raj@rajlog.com'])
      return redirect('thanks', id=9)
    return redirect('thanks', id=1)
  elif request.method == 'POST' and request.POST['instance_type'] == 'Cloud':
    if request.POST['main'] == '':
      form = forms.DownloadForm(request.POST)
      if form.is_valid():

        email_clean = form.cleaned_data['email']
        try:
          cloud_record = models.CloudModel.objects.get(email=email_clean, cloud_url__isnull=False)
        except MultipleObjectsReturned:
          cloud_record = models.CloudModel.objects.filter(email=email_clean, cloud_url__isnull=False).first()
        except ObjectDoesNotExist:
          cloud_record = None

        if not cloud_record:

          try:
            o = OneTimeSecret(settings.OTS_EMAIL, settings.OTS_APIKEY)
            secret = o.share(form.cleaned_data['cloud_password'])
            cloud_password = secret["secret_key"]
          except:
            cloud_password = '__plain__' + str(form.cleaned_data['cloud_password'])

          name_clean = form.cleaned_data['name']
          activation_uuid = str(uuid.uuid1())

          cloud_record = models.CloudModel.objects.create(
            name=name_clean,
            email=email_clean,
            cloud_password=cloud_password,
            ip_address=client_address,
            clicky_cookie=clicky_cookie,
            activation_uuid=activation_uuid,
            request_cookies=request_cookies
          )

          cloud_record.cloud_url = 'https://d42-%s.device42.net/' % format(cloud_record.id, '04')
          cloud_record.save()

          subject = 'Download'
          message2 = """
          Cloud Form Submission

          Name: %s
          Sender: %s
          Cloud Url: %s
          Client IP: %s
          Activated : False
          """ % (name_clean, email_clean, cloud_record.cloud_url, cloud_record.ip_address)

          from_address = 'support@device42.com'
          recipients = ['raj@rajlog.com']
          if settings.DEBUG:
            recipients = ['dave.amato@device42.com', ]
          view_logic.immediate_cloud_activation_send(request, name_clean, email_clean, activation_uuid)
          send_mail(subject, message2, from_address, recipients)
          view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean, email_clean, '', None, None, None, None, True)
          request.session['temp_data'] = form.cleaned_data
          return redirect('thanks', id=12)
        else:
          if not cloud_record.active:
            form.add_error('email', mark_safe('''This email already initialized cloud instance.<br>
                                                 But instance not activated, we resend link, please check email.'''))
            view_logic.immediate_cloud_activation_send(request, cloud_record.name, cloud_record.email, cloud_record.activation_uuid)
          else:
            form.add_error('email', mark_safe('''This email has already initialized a Cloud based instance.<br>
                                              Go to <a href="%s">%s</a> and login with your existing credentials.''' % (cloud_record.cloud_url, cloud_record.cloud_url)))

      return render(request, 'forms/download.html', {'form': form})

  elif request.method == 'POST' and request.POST['instance_type'] == 'Talk-to':
    return schedule_form(request)
  elif 'email' in request.GET:
    form = forms.DownloadForm(initial={'email': request.GET['email']})
  elif 'activation_expired' in request.GET:
    form = forms.DownloadForm({
        'name': request.session['activation_name'] if 'activation_name' in request.session else '',
        'email': request.session['activation_email'] if 'activation_email' in request.session else ''
    })
    form.add_error('email', mark_safe('''Your activation link is expired, please fill the form again.'''))
  else:
    form = forms.DownloadForm()
  return render(request, 'forms/download.html', {'form': form})


@never_cache
def itaas_form(request):
  the_matrix = {'name': '',
                'email': '',
                'vp': '',
                'eula': False,
                'name_error': False,
                'email_error': False,
                'platform_error': False,
                'eula_error': False,
                'errors': False,
                }
  if request.method == 'POST':
    if request.POST['main'] == '':
      form = forms.OtherDownloadsForm(request.POST)
      if form.is_valid():
        the_ref = client_address = clicky_cookie = intercom_id = the_cookie = ''
        if 'HTTP_REFERER' in request.META:
          the_ref = request.META['HTTP_REFERER']
        else:
          the_ref = None
        if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
        if 'hubspotutk' in request.COOKIES: the_cookie = request.COOKIES['hubspotutk']
        if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
        if 'intercom-id' in request.COOKIES:
          intercom_id = request.COOKIES['intercom-id']

        download_uuid = str(uuid.uuid1())
        email_clean = form.cleaned_data['email']
        name_clean = form.cleaned_data['name']
        models.OtherDownloads.objects.create(name=name_clean, email=email_clean,
                                             ip_address=client_address, clicky_cookie=clicky_cookie,)
        subject = 'Download'
        message2 = """
Download Form Submission

Name: %s
Sender: %s
Client IP: %s
""" % (name_clean, email_clean, client_address)

        from_address = 'support@device42.com'
        recipients = ['raj@rajlog.com']
        if settings.DEBUG:
          recipients = ['tolya.double@gmail.com', ]
        view_logic.immediate_download_send(request, name_clean, email_clean, download_uuid)
        send_mail(subject, message2, from_address, recipients)
        view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean,
                                     email_clean, '')
        request.session['temp_data'] = form.cleaned_data

      else:
        return render(request, 'forms/itaas/variant1.html', {'form': form})
    else:
      send_mail('download -ve', str(request.POST), 'support@device42.com', ['raj@rajlog.com'])
      return redirect('thanks', id=9)
    return redirect('thanks', id=1)
  else:
    form = forms.OtherDownloadsForm()
  return render(request, 'forms/itaas/variant1.html', {'form': form})


@never_cache
def idc_form(request):

  if request.method == 'POST':
    form = forms.OtherDownloadsForm(request.POST)
    if form.is_valid():
      client_address = clicky_cookie = intercom_id = ''
      fc = form.save(commit=False)
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
      if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']

      fc.ip_address = client_address
      fc.clicky_cookie = clicky_cookie
      fc.intercom_id = intercom_id
      fc.type = 'ipc-white-paper'
      fc.name = name = form.cleaned_data['name']
      fc.email = to_email = form.cleaned_data['email']
      fc.save()

      the_subject = "Your Device42 IDC white paper is attached."
      from_email = "Device42 Support Team <support@corp.device42.com>"

      text = '''
      Hi %s,

      Attached, please find the white paper you requested, and thank you for your interest in Device42!
      If you aren't currently a Device42 user, give it a try for free! Download here: https://www.device42.com/download/

      Regards,


      The Device42 Team
      ''' % name

      html = '''
      <p>Hi %s,</p>

      <p>Attached, please find the white paper you requested, and thank you for your interest in Device42!<br>If you aren't currently a Device42 user, give it a try for free! Download <a href="https://www.device42.com/download/" target="_blank">here</a>.</p>

      <p>Regards,</p><br>
      <p>The Device42 Team</p>
      ''' % name

      file_name = 'IDC White Paper - IT Agility and business alignment - Why you need an SST.pdf'
      file_path = settings.BASE_DIR + '/static/data/pdf/IDC-White-Paper-IT-Agility-and-business-alignment-Why-you-need-an-SST.pdf'
      files=[("attachment", (file_name, open(file_path, "rb").read())),]

      view_logic.send_mailgun_message(
        from_email, to_email, the_subject, text, html, attached_files=files)

      return redirect('thanks', id=11)
  else:
    form = forms.OtherDownloadsForm()

  return render(request, 'forms/idc.html', {'form': form})


@never_cache
def download_links(request, download_uuid):
  dwnld = models.DownloadModel.objects.filter(download_uuid=download_uuid)
  the_links = []
  error_message = ""
  form = forms.DownloadForm()
  user_name = ""
  if (dwnld.count() == 1):
    #create entry to track page visit
    models.DownloadLinkTrack.objects.create(downloadmodel = dwnld[0])
    links = models.DownloadLinks.objects.filter(downloadmodel=dwnld[0])
    atime = time.mktime(dwnld[0].time_linked.timetuple())
    expires = int(atime) + 7 * 24 * 60 * 60
    if int(time.time()) > expires:
      error_message = _("Your download link has expired")
      form = forms.DownloadForm({'name': dwnld[0].name, 'email': dwnld[0].email})
    elif len(links) == 0:
      the_links = view_logic.generate_download_links(expires)
      for _dict in the_links:
        models.DownloadLinks.objects.create(name=_dict['name'], link=_dict['link'], size=_dict['size'],
                                            downloadmodel=dwnld[0],
                                            img_src=_dict['img_src'])
    else:
      for link in links:
        the_links.append({'name': link.name, 'link': link.link, 'size': link.size, 'img_src': link.img_src})

    user_name = dwnld[0].name
    request.session['download_name'] = dwnld[0].name
    request.session['download_email'] = dwnld[0].email
  else:
    error_message = _("Could not find your download link")
    the_matrix = {'name': '',
                  'email': '',
                  'vp': '',
                  'eula': False,
                  'name_error': False,
                  'email_error': False,
                  'platform_error': False,
                  'eula_error': False,
                  'errors': False,
                  }
    #TODO fix following. dup code. should be using download code.
    if request.method == 'POST':
      if request.POST['main'] == '':
        form = forms.DownloadForm(request.POST)
        if form.is_valid():
          the_ref = client_address = clicky_cookie = intercom_id = the_cookie = ''
          if 'HTTP_REFERER' in request.META:
            the_ref = request.META['HTTP_REFERER']
          else:
            the_ref = None
          if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
          if 'hubspotutk' in request.COOKIES: the_cookie = request.COOKIES['hubspotutk']
          if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
          if 'intercom-id' in request.COOKIES:
            intercom_id = request.COOKIES['intercom-id']
          else:
            the_cookie = None

          request_cookies = request.COOKIES

          download_uuid = str(uuid.uuid1())
          email_clean = form.cleaned_data['email']
          name_clean = form.cleaned_data['name']
          dwnld = models.DownloadModel.objects.create(name=name_clean, email=email_clean,
                                                      I_agree_to_EULA=True, ip_address=client_address,
                                                      download_uuid=download_uuid, clicky_cookie=clicky_cookie,
                                                      request_cookies=request_cookies, )
          subject = 'Download'
          message2 = """Download Form Submission
      Name: %s
      Sender: %s
      Client IP: %s
            """ % (name_clean, email_clean, client_address)

          from_address = 'support@device42.com'
          recipients = ['raj@rajlog.com']
          if settings.DEBUG:
            recipients = ['dave.amato@device42.com', ]
          view_logic.immediate_download_send(request, name_clean, email_clean, download_uuid)
          send_mail(subject, message2, from_address, recipients)
          view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean,
                                       email_clean, '')
        else:
          return render(request, 'sections/download_links.html',
                        {'error_message': error_message, 'the_links': the_links, 'form': form})
      else:
        send_mail('download -ve', str(request.POST), 'support@device42.com', ['raj@rajlog.com'])
        return redirect('thanks', id=9)
      return redirect('thanks', id=1)
    else:
      form = forms.DownloadForm()
  return render(request, 'sections/download_links.html',
                {'error_message': error_message, 'the_links': the_links, 'form': form, 'user_name': user_name})

def cloud_activate_async(request, cloud_record, cloud_password, ots_url):

    ec2 = boto.ec2.connect_to_region(
        "us-east-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    ''' 
    SET CURRENT
    '''
    instance_id = cloud_record.cloud_url[12:].split('.')[0]
    domain = 'd42-' + format(int(instance_id), '04')
    reservation = ec2.get_all_instances(filters={"tag:Name": "cloud-reserve", 'instance-state-name': 'running'})
    instances = [i for r in reservation for i in r.instances]
    instance = instances[0]

    dns_data = {
      'name': domain,
      'value': instance.ip_address,
      'type': 'A',
      'ttl': 60
    }
    try:
      dme = DME2(settings.DME_KEY, settings.DME_SECRET)
      dme.add_record_to_domain(settings.DME_DOMAIN_ID, dns_data)
    except Exception as e:
      send_mail('DME connection error (%s)' % domain, str(e), 'support@device42.com', ['anatolii.chmykhalo@device42.com', 'raj@rajlog.com'])
      print 'dme_error'

    admin_data = {
      'username': cloud_record.email,
      'password': cloud_password,
      'is_superuser': 'yes'
    }
    auth = ('admin', 'rBjJGCx4uiEaNqX7')


    requests.post('https://%s/api/1.0/adminusers/' % instance.ip_address, auth=auth, data=admin_data, verify=False)
    requests.delete('https://%s/api/1.0/adminusers/1/' % instance.ip_address, auth=auth, verify=False)
    instance.add_tag("Name", domain)

    view_logic.immediate_cloud_data_send(request, cloud_record, ots_url)


    '''
    BUILD NEXT INSTANCE
    '''
    interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(
        subnet_id='subnet-f5ae2fbf',
        groups=['sg-e2a75690'],
        associate_public_ip_address=True
    )
    interfaces = boto.ec2.networkinterface.NetworkInterfaceCollection(interface)

    reservation = ec2.run_instances(
        'ami-0180a3b99b68de5c6',
        instance_type='t2.medium',
        network_interfaces=interfaces
    )

    instance = reservation.instances[0]
    time.sleep(300)
    instance.add_tag("Name", 'cloud-reserve')


@never_cache
def cloud_activation(request, activation_uuid):
  try:
    cloud_record = models.CloudModel.objects.get(activation_uuid=activation_uuid)
    if cloud_record.active is False:

      if cloud_record.cloud_password.startswith('__plain__'):
          cloud_password = cloud_record.cloud_password[9:]
          cloud_record.cloud_password = '__plain__'
          cloud_record.save()
      else:
        try:
          o = OneTimeSecret(settings.OTS_EMAIL, settings.OTS_APIKEY)
          cloud_password = o.retrieve_secret(cloud_record.cloud_password)['value']

          # prepare secret for customer view
          secret = o.share(cloud_password)
          secret_metadata = secret["metadata_key"]
          ots_url = o.secret_link(secret_metadata)
        except:
          request.session['activation_name'] = cloud_record.name
          request.session['activation_email'] = cloud_record.email
          cloud_record.delete()
          return redirect(reverse('download') + '?activation_expired')

      cloud_record.active = True
      cloud_record.save()

      # prevent duplicate instance start
      check_records = models.CloudModel.objects.filter(email=cloud_record.email, active=False)
      for record in check_records:
          record.active = True
          record.save()

      '''
      ACTIVATE INSTANCE
      '''
      thread = threading.Thread(target=cloud_activate_async, args=[request, cloud_record, cloud_password, ots_url])
      thread.start()

      return thanks(request, id='13')
    else:
      raise Http404

  except ObjectDoesNotExist:
    raise Http404

def compare(request):
  return render(request, 'sections/compare/_compare.html')


def vs_index_page(request):
  return render(request, 'sections/compare/_vs-index-page.html')


def compare_nlyte(request):
  return render(request, 'sections/compare/nlyte.html')


def compare_sunbird(request):
  return render(request, 'sections/compare/sunbird.html')


def compare_servicenow(request):
  return render(request, 'sections/compare/servicenow.html')

def compare_servicewatch(request):
  return render(request, 'sections/compare/servicewatch.html')

def compare_bmc_atrium(request):
  return render(request, 'sections/compare/bmc-atrium.html')


def compare_hp_ucmdb(request):
  return render(request, 'sections/compare/hp-ucmdb.html')


def compare_solarwinds(request):
  return render(request, 'sections/compare/solarwinds.html')


def compare_infoblox(request):
  return render(request, 'sections/compare/infoblox.html')


def compare_dcim(request):
  return render(request, 'sections/compare/dcim.html')


def compare_ipam(request):
  return render(request, 'sections/compare/ipam.html')


def compare_cmdb(request):
  return render(request, 'sections/compare/cmdb.html')


def compare_risc(request):
  return render(request, 'sections/compare/risc.html')


def compare_bmc_discovery(request):
  return render(request, 'sections/compare/bmc-discovery.html')


def compare_racktables(request):
  return render(request, 'sections/compare/racktables.html')

def compare_insight_jira(request):
  return render(request, 'sections/compare/insight-jira.html')

def compare_cloudamize(request):
  return render(request, 'sections/compare/cloudamize.html')

def compare_lansweeper(request):
  return render(request, 'sections/compare/lansweeper.html')

def compare_glpi(request):
  return render(request, 'sections/compare/glpi.html')

def compare_netterrain(request):
  return render(request, 'sections/compare/netterrain.html')

def compare_manageengine(request):
  return render(request, 'sections/compare/manageengine.html')

def compare_bluecat(request):
  return render(request, 'sections/compare/bluecat.html')

def compare_idoit(request):
  return render(request, 'sections/compare/idoit.html')

def compare_itop(request):
  return render(request, 'sections/compare/itop.html')

def compare_phpipam(request):
  return render(request, 'sections/compare/phpipam.html')

def compare_firescopeddm(request):
  return render(request, 'sections/compare/firescopeddm.html')

def compare_cormant_cs(request):
  return render(request, 'sections/compare/cormant-cs.html')

def videos(request):
  return render(request, 'sections/support/_videos.html', {'videos': _getVideos()})


def videos_introduction(request):
  return render(request, 'sections/support/videos/introduction.html')


def videos_dcim_demo(request):
  return render(request, 'sections/support/videos/quick-demo.html')


def videos_server_room(request):
  return render(request, 'sections/support/videos/server-rooms.html')


def videos_basic_navigation(request):
  return render(request, 'sections/support/videos/basic-navigation.html')


def videos_rack_management(request):
  return render(request, 'sections/support/videos/rack-management.html')


def videos_patch_panel_management(request):
  return render(request, 'sections/support/videos/patch-panel-management.html')


def videos_ip_address_management(request):
  return render(request, 'sections/support/videos/ip-address-management.html')


def videos_hierarchy(request):
  return render(request, 'sections/support/videos/hierarchy.html')


def videos_enterprise_password_management(request):
  return render(request, 'sections/support/videos/enterprise-password-management.html')


def videos_autodiscovery(request):
  return render(request, 'sections/support/videos/autodiscovery.html')


def opensource(request):
  return render(request, 'sections/support/opensource.html')


def software(request):
  utilities = _getUtilities()
  return render(request, 'sections/support/_software.html', {'tools': utilities})

@never_cache
def abs301Redirect(request, token):
  try:
    if token:
      return HttpResponsePermanentRedirect(reverse(token))
    else:
      return HttpResponseRedirect(reverse('home'))
  except:
    return HttpResponseRedirect(reverse('home'))

@never_cache
def software_detail(request, package):
  utilities = _getUtilities()
  if package in utilities.values():
    if (request.method == 'POST') and ('download' in request.POST):
      _download = request.POST.get('download')
      if ('open disc' in _download):
        form = forms.FreeClientForm(request.POST)
        if form.is_valid() and ('main' in request.POST):
          link = view_logic.generate_link_software(package, request, form)
          return HttpResponseRedirect(link)
      elif ('update' in _download):
        form = forms.UpdateForm(request.POST)
        if ('pma' in _download):
          update_type = 'pma'
        else:
          update_type = 'regular'

        if form.is_valid() and (request.POST['main'] == ''):
          link = view_logic.generate_link_software(package, request, form)
          return HttpResponseRedirect(link)
        else:
          return render(request, 'sections/support/_software.html',
                        {'tools': utilities, 'package': package, 'error': update_type})
      else:
        if 'main' in request.POST:
          link = view_logic.generate_link_software(package, request)
          return HttpResponseRedirect(link)
        else:
          # return render(request, 'sections/support/_software.html',
          #               {'tools': utilities, 'package': package})
          if 'main' in request.POST:
            link = view_logic.generate_link_software(package, request)
            return HttpResponseRedirect(link)
          else:
            return render(request, 'sections/support/_software.html', {'tools': utilities, 'package': package})
    else:
      return render(request, 'sections/support/_software.html', {'tools': utilities, 'package': package})
  else:
    return HttpResponseRedirect(reverse('package'))


def integrations(request):
  integrations_object = _getIntegrations()
  integrations_detail = _getIntegrationDetails()

  return render(request, 'sections/support/_integrations.html', {
                  'integrations': integrations_object,
                  'integration_details': sorted(integrations_detail, key=lambda x: x['title'])
                })


@never_cache
def integrations_detail(request, slug):
  print 'getting integration: ', slug
  integrations_object = _getIntegrations()

  if slug in integrations_object.values():
    if request.method == 'POST':
      if slug == "service-now":
        link = "https://api.github.com/repos/device42/servicenow_device42_mapping/zipball"
      elif slug == "servicenow-express":
        link = "https://api.github.com/repos/device42/device42_to_servicenow_express/zipball"
      elif slug == "rundeck":
        link = view_logic.generate_link_generic('d42rundesk-node-1.0.0.jar')
      elif slug == "bmc-remedy":
        link = view_logic.generate_link_generic('d42-bmc_v1.1.zip')
      elif slug == "vmware-vrealize":
        link = view_logic.generate_link_generic('Device42_IPAM.workflow')
      elif slug == "powerbi":
        link = view_logic.generate_link_generic('D42_ODBC_v1.0.zip', 'device42')
      elif slug == "rundeck":
        link = view_logic.generate_link_generic('d42rundesk-node-1.0.0.jar')
      elif slug == "cherwell":
        link = "https://api.github.com/repos/device42/cherwell_device42_sync/zipball"
      elif slug == "bmc-atrium":
        link = "https://github.com/device42/d42-bmc-atrium/archive/master.zip"
      else:
        return HttpResponseRedirect(reverse('integrations'))

      client_address = clicky_cookie = intercom_id = ''
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
      if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']
      # if clicky_cookie: OtherDownloads.objects.create(type='integrations detail', ip_address=client_address,
      #                                                 clicky_cookie=clicky_cookie, intercom_id=intercom_id)
      return HttpResponseRedirect(link)
    print 'rendering: ', slug
    return render(request, 'sections/support/_integrations.html', {'integrations': integrations_object, 'slug': slug})
  else:
    return HttpResponseRedirect(reverse('integrations'))

def migrations(request):
  migrations = _getMigrations()
  return render(request, 'sections/support/_migrations.html', {'migrations': migrations})

def support(request):
  return render(request, 'sections/support/support.html')


@never_cache
def migrations_detail(request, product):
  migrations = _getMigrations()
  response_data = {}
  response_data['status'] = 'ko'

  if product in migrations.values():
    if request.is_ajax():
      try:
        if product == "aperture":
          link = view_logic.generate_link_generic('Aperture-Views_D42-Migration.zip')
        elif product == "opendcim":
          link = "https://github.com/device42/OpenDCIM-to-Device42-Migration/archive/master.zip"
        elif product == "rackmonkey":
          link = "https://github.com/device42/RackMonkey-to-Device42-Migration/archive/master.zip"
        elif product == "racktables":
          link = "https://github.com/device42/Racktables-to-Device42-Migration/archive/master.zip"
        elif product == "solarwinds-ipam":
          link = "https://github.com/device42/SolarWinds_IPAM_to_Device42_Migration/archive/master.zip"

        client_address = request.META.get('REMOTE_ADDR')
        clicky_cookie = request.COOKIES.get('_jsuid')
        intercom_id = request.COOKIES.get('intercom-id')
        if clicky_cookie: models.OtherDownloads.objects.create(type=('%s migration script' % product),
                                                               ip_address=client_address,
                                                               clicky_cookie=clicky_cookie, intercom_id=intercom_id)
        response_data['status'] = 'ok'
        response_data['link'] = link
        return JsonResponse(response_data)
      except:
        response_data['status'] = 'ko'
        response_data['error'] = 'error retrieving download link'
    return render(request, 'sections/support/_migrations.html', {'migrations': migrations, 'product': product})
  else:
    return HttpResponseRedirect(reverse('migrations'))


def partners(request):
  return HttpResponsePermanentRedirect('/partner-benefits/');


def partners_benefits(request):
  return render(request, 'sections/partners/partners_benefits.html')


def partners_learnmore(request):
  return render(request, 'sections/partners/partners_learnmore.html')


def partners_register(request):
  return render(request, 'sections/partners/partners_register.html')


def partners_find(request):
  return render(request, 'sections/partners/partners_find.html')


def tours(request):
  return render(request, 'sections/tours/_tours.html')


def tours_patch_cable_management(request):
  return render(request, 'sections/tours/cable-management.html')


def tours_it_inventory_management(request):
  return render(request, 'sections/tours/it-inventory-management-software.html')


def tours_data_center_power_management(request):
  return render(request, 'sections/tours/data-center-power-management.html')


def tours_ip_address_tracking_software(request):
  return render(request, 'sections/tours/ip-address-tracking-software.html')


def tours_ssl_certificate_management(request):
  return render(request, 'sections/tours/ssl-certificate-management.html', {})

def tours_iso27001_compliance(request):
  return render(request, 'sections/tours/iso27001-compliance.html', {})


def tours_server_room_management(request):
  return render(request, 'sections/tours/server-room-management.html')


def tours_data_center_documentation(request):
  return render(request, 'sections/tours/data-center-documentation.html')


def tours_history_logs(request):
  return render(request, 'sections/tours/history-logs.html')


def tours_manage_spare_parts(request):
  return render(request, 'sections/tours/manage-spare-parts.html')


def tours_server_inventory(request):
  return render(request, 'sections/tours/server-inventory.html')


def tours_server_rack_diagrams(request):
  return render(request, 'sections/tours/server-rack-diagrams.html')

def tours_cloud_migration(request):
  return render(request, 'sections/tours/cloud-migration.html')

def application_sql_migration(request):
  return render(request, 'sections/tours/application-sql-migration.html')

def roi_calculator(request):
  return render(request, 'components/roi-calculator.html', {})


@never_cache
def offers(request, partner=None):
  if partner and partner in ['metabyte', 'cambridge-computer', 'accudata-systems', 'yandree', ]:
    return render(request, 'base/_base-partner.html', {'partner': partner})
  else:
    raise Http404


def lisa16(request):
  form = None
  if request.method == 'POST':
    form = forms.OtherDownloadsForm(request.POST)

    if form.is_valid():
      client_address = clicky_cookie = intercom_id = ''
      fc = form.save(commit=False)
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
      if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']

      fc.ip_address = client_address
      fc.clicky_cookie = clicky_cookie
      fc.intercom_id = intercom_id
      fc.type = 'lisa16'
      fc.name = name = form.cleaned_data['name']
      fc.email = email = form.cleaned_data['email']
      fc.ip_address = client_address
      fc.save()
      subject = 'LISA16 - Download Request'
      message2 = '''
        LISA Attendee - Download Request
        Name: %s
        Sender: %s
        Client IP: %s
                ''' % (name, email, client_address)
      fc.save()
      from_address = 'support@device42.com'
      recipients = ['sales@device42.com']
      if settings.DEBUG:
        recipients = ['dave.amato@device42.com']
      send_mail(subject, message2, from_address, recipients)
      request.session['temp_data'] = form.cleaned_data
      return thanks(request, id='10')
    else:
      return render(request, 'forms/client_promos/lisa16.html', {'form': form})
  else:
    form = forms.OtherDownloadsForm()

  return render(request, 'forms/client_promos/lisa16.html', {'form': form})

def koozie(request):
  form = None
  if request.method == 'POST':
    form = forms.OtherDownloadsForm(request.POST)

    if form.is_valid():
      client_address = clicky_cookie = intercom_id = ''
      fc = form.save(commit=False)
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
      if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']

      fc.ip_address = client_address
      fc.clicky_cookie = clicky_cookie
      fc.intercom_id = intercom_id
      fc.type = 'koozie'
      fc.name = name = form.cleaned_data['name']
      fc.email = email = form.cleaned_data['email']
      fc.ip_address = client_address
      fc.save()
      subject = 'LISA17 - Download Request'
      message2 = '''
        LISA Attendee - Download Request
        Name: %s
        Sender: %s
        Client IP: %s
                ''' % (name, email, client_address)
      fc.save()
      from_address = 'support@device42.com'
      recipients = ['sales@device42.com']
      if settings.DEBUG:
        recipients = ['dave.amato@device42.com']
      send_mail(subject, message2, from_address, recipients)
      request.session['temp_data'] = form.cleaned_data
      return thanks(request, id='10')
    else:
      return render(request, 'forms/client_promos/lisa17.html', {'form': form})
  else:
    form = forms.OtherDownloadsForm()

  return render(request, 'forms/client_promos/lisa17.html', {'form': form})

def cyberlogic_solutions(request):
  form = None

  if request.method == 'POST':
    form = forms.OtherDownloadsForm(request.POST)

    if form.is_valid():
      client_address = clicky_cookie = intercom_id = ''
      fc = form.save(commit=False)
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
      if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']

      fc.ip_address = client_address
      fc.clicky_cookie = clicky_cookie
      fc.intercom_id = intercom_id
      fc.type = 'cyberlogic-solutions'
      fc.name = name = form.cleaned_data['name']
      fc.email = email = form.cleaned_data['email']
      fc.ip_address = client_address
      fc.save()

      subject = 'Cyberlogic Solutions - Download Request'
      message2 = '''
        Cyberlogic Solutions - Download Request
        Name: %s
        Sender: %s
        Client IP: %s
                ''' % (name, email, client_address)
      from_address = 'support@device42.com'
      recipients = ['cyberlogic@device42.com']
      if settings.DEBUG:
        recipients = ['dave.amato@device42.com']
      send_mail(subject, message2, from_address, recipients)
      request.session['temp_data'] = form.cleaned_data

      return thanks(request, id='10')

  else:
    form = forms.OtherDownloadsForm()

  return render(request, 'forms/client_promos/cyberlogic_solutions.html', {'form': form})

def lisa_survey_results(request):
  return render(request, 'sections/lisa-2017-survey-results.html', {})

@never_cache
def it_coloring_book(request):
  if request.method == 'POST':
    link = view_logic.generate_link_generic('Device42-IT-Coloring-Book.pdf')
    client_address = clicky_cookie = intercom_id = ''
    if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
    if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
    if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']
    if clicky_cookie: models.OtherDownloads.objects.create(type='it adult coloring book', ip_address=client_address,
                                                           clicky_cookie=clicky_cookie, intercom_id=intercom_id)
    return HttpResponseRedirect(link)
  else:
    return render(request, 'sections/it-coloring-book.html', {})


def vulndb(request):
  if request.method == 'POST':
    form = forms.OtherDownloadsForm(request.POST)

    if form.is_valid():
      client_address = clicky_cookie = intercom_id = ''
      fc = form.save(commit=False)
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
      if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']

      fc.ip_address = client_address
      fc.clicky_cookie = clicky_cookie
      fc.intercom_id = intercom_id
      fc.type = 'vulndb'
      fc.name = form.cleaned_data['name']
      fc.email = form.cleaned_data['email']
      fc.ip_address = client_address
      fc.save()

      request.session['temp_data'] = form.cleaned_data
      return thanks(request, id='7')
    else:
      return render(request, 'sections/vulndb.html', {'form': form})
  else:
    form = forms.OtherDownloadsForm()

  return render(request, 'sections/vulndb.html', {'form': form})


from django.views.decorators.csrf import ensure_csrf_cookie
@never_cache
@ensure_csrf_cookie
def power_appliance(request):
  platforms = _getPowerPlatforms()
  if request.method == 'POST':
    sender = request.POST['email']
    platform = request.POST['platform']
    if sender and (sender.split('@')[1] not in INCOGNITO_LIST):
      view_logic.immediate_power_send(sender, platform, platforms[platform])
      temp_data = {
        'email': sender,
      }
      request.session['temp_data'] = temp_data
      return redirect('thanks', id=2)
    else:
      return render(request, 'sections/power-appliance-download.html', {'form_errors':'true', 'platforms': platforms })
  return render(request, 'sections/power-appliance-download.html', {'platforms': platforms })

@never_cache
def vulnerability_management_software(request):
  if request.method == 'POST':
    form = forms.OtherDownloadsForm(request.POST)

    if form.is_valid():
      fc = form.save(commit=False)
      client_address = clicky_cookie = intercom_id = ''
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
      if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']
      fc.clicky_cookie = clicky_cookie
      fc.intercom_id = intercom_id
      fc.name = form.cleaned_data['name']
      fc.email = form.cleaned_data['email']
      fc.ip_address = client_address
      fc.type = 'vulndb'
      form.save()

      request.session['temp_data'] = form.cleaned_data
      return redirect('thanks', id=7)
  else:
    form = forms.OtherDownloadsForm()
  return render(request, 'sections/features/vulnerability-management-software.html', {'form': form})

def register_for_webinar(request):

  if request.method == 'POST':
    form_class = forms.WebinarRegistrationForm(request.POST)

    if form_class.is_valid():
      client_address = clicky_cookie = intercom_id = ''
      fc = form_class.save(commit=False)
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
      if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']
      the_ref = request.META.get('HTTP_REFERER', None)
      the_cookie = request.COOKIES.get('hubspotutk', None)

      fc.ip_address = client_address
      fc.clicky_cookie = clicky_cookie
      fc.intercom_id = intercom_id
      fc.type = 'webinar-registration'
      fc.first_name = first_name = form_class.cleaned_data['first_name']
      fc.last_name = last_name = form_class.cleaned_data['last_name']
      fc.email = email = form_class.cleaned_data['email']
      fc.title = title = form_class.cleaned_data['title']
      fc.ip_address = client_address
      fc.save()

      view_logic.hubspot_webinar_registration_data_send("webinar_registration", the_cookie, client_address, the_ref, first_name, last_name, email, title)

      return redirect('register_for_webinar_complete')
  else:
    form_class = forms.WebinarRegistrationForm()
  return render(request, 'landing/Device42-register-for-webinar.html', {
    'form': form_class
  })

def register_for_webinar_complete(request):
  return render(request, 'landing/Device42-register-for-webinar-complete.html')

def register_for_webinar2(request):

  if request.method == 'POST':
    form_class = forms.WebinarRegistrationForm(request.POST)

    if form_class.is_valid():
      client_address = clicky_cookie = intercom_id = ''
      fc = form_class.save(commit=False)
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
      if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']
      the_ref = request.META.get('HTTP_REFERER', None)
      the_cookie = request.COOKIES.get('hubspotutk', None)

      fc.ip_address = client_address
      fc.clicky_cookie = clicky_cookie
      fc.intercom_id = intercom_id
      fc.type = 'webinar2-registration'
      fc.first_name = first_name = form_class.cleaned_data['first_name']
      fc.last_name = last_name = form_class.cleaned_data['last_name']
      fc.email = email = form_class.cleaned_data['email']
      fc.title = title = form_class.cleaned_data['title']
      fc.ip_address = client_address
      fc.save()

      view_logic.hubspot_webinar_registration_data_send("webinar2_registration", the_cookie, client_address, the_ref, first_name, last_name, email, title)

      return redirect('register_for_webinar2_complete')
  else:
    form_class = forms.WebinarRegistrationForm()
  return render(request, 'landing/Device42-register-for-webinar2.html', {
    'form': form_class
  })

def register_for_webinar2_complete(request):
  return render(request, 'landing/Device42-register-for-webinar2-complete.html')

def register_for_webinar3(request):

  if request.method == 'POST':
    form_class = forms.WebinarRegistrationForm(request.POST)

    if form_class.is_valid():
      client_address = clicky_cookie = intercom_id = ''
      fc = form_class.save(commit=False)
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
      if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']
      the_ref = request.META.get('HTTP_REFERER', None)
      the_cookie = request.COOKIES.get('hubspotutk', None)

      fc.ip_address = client_address
      fc.clicky_cookie = clicky_cookie
      fc.intercom_id = intercom_id
      fc.type = 'webinar3-registration'
      fc.first_name = first_name = form_class.cleaned_data['first_name']
      fc.last_name = last_name = form_class.cleaned_data['last_name']
      fc.email = email = form_class.cleaned_data['email']
      fc.title = title = form_class.cleaned_data['title']
      fc.ip_address = client_address
      fc.save()

      view_logic.hubspot_webinar_registration_data_send("webinar3_registration", the_cookie, client_address, the_ref, first_name, last_name, email, title)

      return redirect('register_for_webinar3_complete')
  else:
    form_class = forms.WebinarRegistrationForm()
  return render(request, 'landing/Device42-register-for-webinar3.html', {
    'form': form_class
  })

def register_for_webinar3_complete(request):
  return render(request, 'landing/Device42-register-for-webinar3-complete.html')

def automating_servicenow_registeration(request):

  if request.method == 'POST':
    form_class = forms.SecondWebinarRegistrationForm(request.POST)

    if form_class.is_valid():
      client_address = clicky_cookie = intercom_id = ''
      fc = form_class.save(commit=False)
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
      if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']
      the_ref = request.META.get('HTTP_REFERER', None)
      the_cookie = request.COOKIES.get('hubspotutk', None)

      fc.ip_address = client_address
      fc.clicky_cookie = clicky_cookie
      fc.intercom_id = intercom_id
      fc.type = 'second-webinar-registeration'
      fc.email = email = form_class.cleaned_data['email']
      fc.save()

      view_logic.hubspot_webinar_registration_data_send("second_webinar_registeration", the_cookie, client_address, the_ref, "", "", email, "")

      return redirect('thank_you_for_registering')
  else:
    form_class = forms.SecondWebinarRegistrationForm()
    return render(request, 'landing/Device42-webinar-registeration.html', {
      'form': form_class
    })

def thank_you_for_registering(request):
  return render(request, 'landing/Device42-thank-you-for-registering.html')


@never_cache
@require_POST
def ajax_post(request):
  '''
  AJAX Handler for: Contact, ScheduleDemo, and Download forms
  Indicated by the POST request var 'action'
  '''
  action = request.POST.get('action', None)

  STATUS = "ko"
  response_data = {}
  from_address = 'support@device42.com'

  if request.is_ajax() and action == 'schedule':
    try:
      recipients = ['scanelli@device42.com', 'al.rossini@device42.com', ]
      recipients_alt = ['raj@rajlog.com', ]
      recipients_DEV = ['dave.amato@device42.com', ]
      main = request.POST.get('main')

      if main == '':
        form = forms.ScheduleForm(request.POST)
        if form.is_valid():
          fc = form.save(commit=False)

          the_cookie = request.META.get('hubspotutk', None)
          fc.ip_address = client_address = request.META.get('REMOTE_ADDR', '')
          fc.clicky_cookie = request.META.get('_jsuid', '')
          fc.intercom_id = request.META.get('intercom-id', '')
          the_ref = request.META.get('HTTP_REFERER', None)

          fc.name = name = form.cleaned_data['name']
          fc.email = sender = form.cleaned_data['email']
          fc.phone = phone = form.cleaned_data['phone']

          fc.save()

          subject = "FYI: Online Demo - %s - already sent an invite " % sender

          message2 = '''

    	Name: %s
    	Sender: %s
    	Phone: %s
    	IP: %s

    	''' % (name, sender, phone, client_address)

          if settings.DEBUG:
            recipients = recipients_DEV
            recipients_alt = recipients_DEV

          send_mail(subject, message2, from_address, recipients)

          if not settings.DEBUG:
            view_logic.immediate_schedule_demo_send(name, sender)
            view_logic.hubspot_data_send('schedule_demo', the_cookie, client_address, the_ref, name, sender, None, None,
                                         None, phone)

          request.session['temp_data'] = form.cleaned_data
          response_data['status'] = 'ok'
      else:
        response_data['status'] = 'ko'
        response_data['error'] = 'main was not empty'
        send_to = recipients_alt

        if settings.DEBUG:
          send_to = recipients_DEV

        send_mail('demo -ve', str(request.POST), from_address, send_to)
    except:
      pass
  elif request.is_ajax() and action == 'trial':
    try:
      main = request.POST.get('main')
      form = forms.DownloadForm(request.POST)
      if main == '' and form.is_valid():
        fc = form.save(commit=False)

        the_cookie = request.META.get('hubspotutk', None)
        client_address = fc.ip_address = request.META.get('REMOTE_ADDR', '')
        clicky_cookie = fc.clicky_cookie = request.META.get('_jsuid', '')
        intercom_id = fc.intercom_id = request.META.get('intercom-id', '')
        the_ref = request.META.get('HTTP_REFERER', None)
        name = fc.name = form.cleaned_data['name']
        email = fc.email = form.cleaned_data['email']

        if view_logic.get_validate(email) == False:
          response_data['error_msg'] = _("Please use a valid work email address")
          response_data['error'] = 'not-valid-email'
          response_data['status'] = 'ko'
        elif name == '' or email == '':
          response_data['error_msg'] = _("Please fill out all required fields")
          response_data['status'] = 'ko'
          response_data['error'] = 'required field'
        else:
          response_data['status'] = 'ok'
          download_uuid = str(uuid.uuid1())
          dwnld = models.DownloadModel(name=name, email=email, ip_address=client_address, download_uuid=download_uuid,
                                       clicky_cookie=clicky_cookie, intercom_id=intercom_id)
          subject = 'Download'
          message2 = '''
  Download Form
  Name: %s
  Sender: %s
  Client IP: %s
          ''' % (name, email, client_address)
          fc.save()
          from_address = 'support@device42.com'
          recipients = ['raj@rajlog.com']
          if settings.DEBUG:
            recipients = [str(email) for i, email in settings.ADMINS]
          else:
            view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name, email)

          view_logic.immediate_download_send(request, name, email, download_uuid)
    except:
      response_data['status'] = 'ko'
      response_data['error'] = 'could not process'
      response_data['error_msg'] = _("There was an error while processing your request.   Please try again later.")
      pass
  elif request.is_ajax() and action == 'contact':
    try:
      main = request.POST.get('main')
      form = forms.ContactForm(request.POST)
      if main == '' and form.is_valid():
        fc = form.save(commit=False)

        the_cookie = request.META.get('hubspotutk', None)
        client_address = fc.ip_address = request.META.get('REMOTE_ADDR', '')
        clicky_cookie = fc.clicky_cookie = request.META.get('_jsuid', '')
        intercom_id = fc.intercom_id = request.META.get('intercom-id', '')
        the_ref = request.META.get('HTTP_REFERER', None)
        name = fc.name = form.cleaned_data['name']
        email = fc.email = form.cleaned_data['email']
        phone = fc.phone = form.cleaned_data['phone']
        topic = fc.topic = form.cleaned_data['topic']
        message = fc.message = form.cleaned_data['message']

        if view_logic.get_validate(email) == False:
          response_data['error_msg'] = _("Please use a valid work email address")
          response_data['error'] = 'not-valid-email'
          response_data['status'] = 'ko'
        else:
          if topic == '':
            topic = 'General'

          message2 = '''

            Name: %s
            Sender: %s
            Phone: %s
            Topic: %s
            Message: %s
            IP: %s

          ''' % (name, email, phone, topic, message, client_address)

          recipients = ['raj@rajlog.com', 'scanelli@device42.com', ]
          recipients_alt = ['raj@rajlog.com', ]
          recipients_DEV = ['dave.amato@device42.com', ]

          if settings.DEBUG:
            recipients = recipients_DEV
            recipients_alt = recipients_DEV
          else:
            fc.save()
            view_logic.hubspot_data_send('contact', the_cookie, client_address, the_ref, name, email, topic, message,
                                         phone)
          response_data['status'] = 'ok'

          send_mail('Contact Page [%s]' % topic, message2, from_address, recipients)
      else:
        response_data['status'] = 'ko'
        response_data['error'] = 'form not valid'
        if name == '' or email == '' or topic == '':
          response_data['error'] = 'required field'

        if settings.DEBUG:
          recipients_alt = recipients_DEV
        send_mail('contact -ve', message2, from_address, recipients_alt)
    except Exception, e:
      response_data['status'] = 'ko'
      response_data['error'] = 'error processing email'
      response_data['server_error'] = e
      print e
      pass
  return JsonResponse(response_data)


def _getMigrations():
  MIGRATIONS = {
    'Aperture VISTA': 'aperture',
    'SolarWinds IPAM': 'solarwinds-ipam',
    'OpenDCIM': 'opendcim',
    'RackTables': 'racktables',
    'RackMonkey': 'rackmonkey',
    'phpIPAM': 'phpipam',
  }
  return MIGRATIONS


def _getIntegrationDetails():
  INTEGRATION_LOGOS = "img/customers/integrations/%s.png"

  return ({
            "title": "Jira",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'jira'),
            "description": _(
              "Connect your Device42 assets directly to your Jira tickets, syncing data between the Device42 CMDB and Jira Software and/or Jira Service Desk."),
            "link1": resolve_url(integrations_detail, 'jira'),
            "link2": resolve_url(integrations_detail, 'jira-cloud')
          },
          {
            "title": "Microsoft SCCM",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'sccm'),
            "description": _(
              "Already have Microsoft Systems Center Configuration Manager (SCCM) set up and populated with an inventory of all or a majority of your systems? Avoid duplicate auto-discovery, and take advantage of the D42-SCCM Integration to pull existing data and CIs directly into Device42."),
            "link": resolve_url(integrations_detail, 'sccm')
          },
          {
            "title": "Jenkins",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'jenkins'),
            "description": _(
              "With the Device42 - Jenkins credentials integration, users can leverage their passwords and/or other secrets stored securely in Device42 by inserting variables into their Jenkins-based automation, e.g. continuous integration, development & build processes, custom scripts, and more."),
            "link": resolve_url(integrations_detail, 'jenkins')
          },
          {
            "title": "PowerBI",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'powerbi'),
            "description": _(
              "With the Device42 - PowerBI integration, users can connect to Device42's comprehensive CMDB via ODBC and can create reports, dashboards, and extract business intelligence directly from their IT asset database."),
            "link": resolve_url(integrations_detail, 'powerbi')
          },
          {
            "title": "ServiceNow",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'servicenow'),
            "description": _(
              "Using the Device42 - ServiceNow integration connector, ServiceNow users can synchronize Device42's enhanced asset management and tracking capabilities to their ServiceNow configuration items (CI) data maintained inside ServiceNow's Configuration Management Database (CMDB)."),
            "link": resolve_url(integrations_detail, 'service-now')
          },
          {
            "title": "ServiceNow Express",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'servicenow-express'),
            "description": _(
              "Using the Device42 - ServiceNow Express Sync Script integration, ServiceNow Express users can synchronize Device42's enhanced asset management and tracking capabilities to their ServiceNow Express instance."),
            "link": resolve_url(integrations_detail, 'servicenow-express')
          },
          {
            "title": "Rundeck",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'rundeck'),
            "description": _(
              "This integration allows for Rundeck automation to be orchestrated using up-to-date Device42 CMDB information."),
            "link": resolve_url(integrations_detail, 'rundeck')
          },
          {
            "title": "Confluence",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'confluence'),
            "description": _(
              "Integrate with Atlassian Confluence and embed Device42 devices directly into Confluence articles with three powerful custom macros: device links, device details, and device table macros. Put your actual devices into Confluence."),
            "link": resolve_url(integrations_detail, 'confluence')
          },
          {
            "title": "BMC Remedy",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'bmc-remedy'),
            "description": _(
              "If you are using BMC Remedy for your ITSM or even as a part of your ITIL framework- one of the biggest challenges is keeping the configuration item info up-to-date."),
            "link": resolve_url(integrations_detail, 'bmc-remedy')
          },
          {
            "title": "Zendesk",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'zendesk'),
            "description": _(
              "Easily add this free module to your Zendesk installation via the Zendesk Marketplace, and begin including accurate Device42 CI in your Zendesk tickets today!"),
            "link": resolve_url(integrations_detail, 'zendesk')
          },
          {
            "title": "Samanage",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'samanage'),
            "description": _("Leverage Device42's enhanced asset management and tracking capabilities and effortlessly sync data from Device42 to Samanage!"),
            "link": resolve_url(integrations_detail, 'samanage')
          },
          {
            "title": "StackStorm",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'stackstorm'),
            "description": _(
              "StackStorm is a powerful if-this-then-that type tool that helps you automate your workflows and changes to your infrastructure based on predefined 'trigger' criteria taking place anywhere across your environment."),
            "link": resolve_url(integrations_detail, 'stackstorm')
          },
          {
            "title": "Zapier",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'zapier'),
            "description": _(
              "Zapier is a powerful workflow automation with a simple if-this-then-that user interface.  It makes workflow automation easier by enabling changes to be made to your infrastructure based on predefined 'triggers' that can occur anywhere across your environment."),
            "link": resolve_url(integrations_detail, 'zapier')
          },
          {
            "title": "Infoblox",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'infoblox'),
            "description": _(
              "Enhance your IPAM with the InfoBlox / Device42 integration.  Easily utilize this free script to gather information from an Infoblox installation and send it to your Device42 appliance via the REST APIs."),
            "link": resolve_url(integrations_detail, 'infoblox')
          },
          {
            "title": "Ansible",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'ansible'),
            "description": _(
              "With Device42 integration, Ansible has near real-time access to your infrastructure's inventory, making it an even more capable automation solution."),
            "link": resolve_url(integrations_detail, 'ansible')
          },
          {
            "title": "Foreman",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'foreman'),
            "description": _("The Foreman-sync integration can populate Device42 with CI details pulled directly from the Foreman, while the Smart-proxy plugin enables Device42 as a Foreman DHCP provider!"),
            "link1": resolve_url(integrations_detail, 'foreman'),
            "link2": resolve_url(integrations_detail, 'foreman-smart-proxy')
          },
          {
            "title": "Puppet",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'puppet'),
            "description": _("Quickly and Easily Sync Puppet Facts to Device42, and/or Leverage Device42 as a Puppet ENC and Assign Puppet Classes Directly from Device42!"),
            "link": resolve_url(integrations_detail, 'puppet')
          },
          {
            "title": "Chef",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'chef'),
            "description": _("Easily visualize the details of your Chef-powered deployment and its dependencies with Device42. Automatically Import Chef Ohai Node Data Into Device42, and configure Device42 to automatically sync anytime Chef deploys!"),
            "link": resolve_url(integrations_detail, 'chef')
          },
          {
            "title": "SaltStack",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'saltstack'),
            "description": _("With the Device42 Salt Integration, you can now gather information about your devices from the same tool you use to provision them. Also, utilize Salt Pillars for two-way configuration and sync!"),
            "link": resolve_url(integrations_detail, 'saltstack')
          },
          {
            "title": "HPSM",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'hpsm'),
            "description": _("HP Service Manager Sync Script integration, HP Service Manager users can synchronize Device42's enhanced asset management, change management, and tracking capabilities to their HP Service Manager instance."),
            "link": resolve_url(integrations_detail, 'hpsm')
          },
          {
            "title": "VMWare vRealize",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'vrealize'),
            "description": _("With the Device42 VMWare vRealize IPAM Template, VM's are automatically supplied with available IP addresses as your vRealize workflow deploys them."),
            "link": resolve_url(integrations_detail, 'vmware-vrealize')
          },
          {
            "title": "Cherwell",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'cherwell'),
            "description": _(
              "Using the Device42 - Cherwell integration connector, Cherwell users can synchronize Device42's enhanced asset management and tracking capabilities to their Cherwell Configuration Management Database (CMDB)."),
            "link": resolve_url(integrations_detail, 'cherwell')
          },
          {
            "title": "Logstash",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'logstash'),
            "description": _(
              "Offload your Device42 logs to Logstash and benefit from better event correlation by having all your logs in the same, searchable place! Correlating events around your infrastructure has never been easier!"),
            "link": resolve_url(integrations_detail, 'logstash')
          },
          {
            "title": "BMC Atrium",
            "image": staticfiles_storage.url(INTEGRATION_LOGOS % 'bmc-atrium'),
            "description": _(
              "Populating BMC Atrium manually just isn't realistic. Let Device42 handle discovery for you."),
            "link": resolve_url(integrations_detail, 'bmc-atrium')
          }
  )


def _getVideos():
  VIDEOS = ({
              "slug": "dcim-demo",
              "title": _("Device42 DCIM Quick Demo"),
              "image": staticfiles_storage.url("img/sections/support/videos/Device42-DCIM-demo.png"),
              "description": _("Watch a Quick Device42 DCIM functionality demo. Duration ~ 12 minutes."),
              "video_id": "4wf363hrwr",
            },
            {
              "slug": "hierarchy",
              "title": _("Hierarchy"),
              "image": staticfiles_storage.url("img/sections/support/videos/hierarchy.png"),
              "description": _("Gain a basic understanding of Device42's hierarchy and terminology."),
              "video_id": "5ic4mi3xmq",
            },
            {
              "slug": "basic-navigation",
              "title": _("Basic Navigation"),
              "image": staticfiles_storage.url("img/sections/support/videos/basic-navigation.png"),
              "description": _(
                "Basic navigation explains the simple and consistent user interface in Device42. The video introduces Device42's navigation, including list views, search, filter, and bulk actions. See how easy it is to manage your IT Infrastructure."),
              "video_id": "vzjs61pdgj",
            },
            {
              "slug": "server-rooms",
              "title": _("Server Rooms"),
              "image": staticfiles_storage.url("img/sections/support/videos/server-rooms.png"),
              "description": _(
                "An overview of rooms in Device42, including room details, room layout view, and features like drag and drop."),
              "video_id": "s1a7jglham",
            },
            {
              "slug": "managing-racks",
              "title": _("Rack Management"),
              "image": staticfiles_storage.url("img/sections/support/videos/managing-racks.png"),
              "description": _("Web based rack layouts with drag and drop support."),
              "video_id": "hwni7jvebp"
            },
            {
              "slug": "patch-panel-management",
              "title": _("Patch Panel Management"),
              "image": staticfiles_storage.url("img/sections/support/videos/patch-panel-management.png"),
              "description": _("Cable Management with web based interface."),
              "video_id": "q29whe46w5",
            },
            {
              "slug": "ip-address-management",
              "title": _("IP Address Management"),
              "image": staticfiles_storage.url("img/sections/support/videos/switch_impact_chart.png"),
              "description": _(
                "IP Address Management(IPAM) with IPv4/IPv6 and overlapping IP ranges support with Device42."),
              "video_id": "t73hcu61mj",
            },
            {
              "slug": "enterprise-password-management",
              "title": _("Enterprise Password Management"),
              "image": staticfiles_storage.url("img/sections/support/videos/enterprise-password-management.png"),
              "description": _("Manage network passwords securely with granular permission control."),
              "video_id": "uul9xu341e",
            },
            {
              "slug": "autodiscovery",
              "title": _("Device42 Auto-discovery Introduction"),
              "image": staticfiles_storage.url("img/sections/support/videos/Device42-auto-discovery-process.png"),
              "description": _(
                "This video Introduces Device42 IT infrastructure management software's auto-discovery functionality. In this video we will discuss the process of auto-discovery, the best practices for running the initial Device42 auto-discovery, and demonstrate how discoveries build a comprehensive, accurate asset database in Device42 DCIM software. We'll also address a few frequently asked questions and provide links to additional auto-discovery resources."),
              "video_id": "qr7ght1mcz",
            })
  return VIDEOS


def _getUtilities():
  UTILITIES = {
    _('Auto Discovery'): 'autodiscovery',
    _('Update'): 'update',
    _('Bulk Data Management'): 'bulk-data-management',
    # _('Device42 Download'): 'device42-download',
    _('Miscellaneous Tools'): 'miscellaneous-tools',
  }
  return UTILITIES


def _getIntegrations():
  return {
    'Jira': 'jira',
    'Jira Service Desk': 'jira-cloud',
    'Confluence': 'confluence',
    'ServiceNow': 'service-now',
    'ServiceNow Express': 'servicenow-express',
    'Rundeck': 'rundeck',
    'Zendesk': 'zendesk',
    'Microsoft SCCM': 'sccm',
    'BMC Remedy': 'bmc-remedy',
    'StackStorm': 'stackstorm',
    'Zapier': 'zapier',
    'Infoblox': 'infoblox',
    'Ansible': 'ansible',
    'Foreman': 'foreman',
    'Foreman Smart-Proxy': 'foreman-smart-proxy',
    'Puppet': 'puppet',
    'Chef': 'chef',
    'SaltStack': 'saltstack',
    'HPSM': 'hpsm',
    'VMWare vRealize': 'vmware-vrealize',
    'Cherwell': 'cherwell',
    'Logstash': 'logstash',
    'BMC Atrium': 'bmc-atrium',
    'Samanage': 'samanage',
    'PowerBI': 'powerbi',
    'Jenkins': 'jenkins',
  }


def _getClientLogos():
  LOGOS = CLIENT_LOGOS = {
    "ucsb": "ucsb.png",
    "fijitsu": "fijitsu.png",
    "mercedesbenz": "mercedesbenz.png",
    "westerndigital": "westerndigital.png",
    "qlik": "qlik.png",
    "jasper": "jasper.png",
    "bt": "bt.png",
    "singtel": "singtel.png",
    "apptio": "apptio.png",
    "homeaway": "homeaway.png",
    "mitre": "mitre.png",
    "livingsocial": "livingsocial.png",
    "concur": "concur.png",
    "fifgroup": "fifgroup.png",
    "bottomline": "bottomline.png",
    "optus": "optus.png",
    "pico": "pico.png",
    "peak6": "peak6.png",
    "atlassian": "atlassian.png",
    "sprint": "sprint.png",
    "verizon": "verizon.png",
    "stackoverflow": "stackoverflow.png",
    "schoolofbeijing": "schoolofbeijing.png",
    "avaya": "avaya.png",
    "crowdstrike": "crowdstrike.png",
    "appdirect": "appdirect.png",
    "maxihost": "maxihost.png"
  };
  return LOGOS


def _getJobs():
  return {
    0: _("DevOps Evangelist"),
  }

def _getPowerPlatforms():
  return {
    'vmware': 'VMware ESXi',
    'vmdk': 'VMDK',
    'xen': 'Citrix Xen',
    'KVM': 'KVM Xen',
    'vhd': 'Hyper-V VHD',
  }

class AjaxDownloadFill(View):
  def post(self, request):
    the_matrix = {'name': '',
                  'email': '',
                  'vp': '',
                  'eula': 'on',
                  'name_error': False,
                  'email_error': False,
                  'platform_error': False,
                  'eula_error': False,
                  'errors': False,
                  }
    if 'main' in request.POST and 'email' in request.POST and 'name' in request.POST and 'csrftoken' in request.POST and \
        request.POST['main'] == '':
      if 'CSRF_COOKIE' in request.META and request.META['CSRF_COOKIE'] == request.POST['csrftoken']:
        the_email = request.POST['email']
        the_validation = True
        if '@' not in the_email:
          the_validation = False
          the_matrix['email_error'] = True
          return Response(500, content={'code': 0, 'msg': the_matrix, 'validation': the_validation})
        domain_lower = the_email.split('@')[1].lower()
        if (domain_lower in INCOGNITO_LIST) or ('yahoo.' in domain_lower):
          the_validation = False
          the_matrix['email_error'] = True
          client_address = title = clicky_cookie = intercom_id = ''
          if 'REMOTE_ADDR' in request.META:
            client_address = request.META['REMOTE_ADDR']
          if 'title' in request.POST:
            title = request.POST['title']
          if '_jsuid' in request.COOKIES:
            clicky_cookie = request.COOKIES['_jsuid']
          the_type = 'download'
          if 'type' in request.POST and request.POST['type'] == 'demo':
            the_type = 'demo'
          IncognitoDownloads.objects.create(name=request.POST['name'],
                                            email=the_email,
                                            ip_address=client_address,
                                            clicky_cookie=clicky_cookie,
                                            tipe=the_type,
                                            title=title,
                                            post_data=request.POST,
                                            meta_data=request.META)
          return Response(500, content={'code': 0, 'msg': the_matrix, 'validation': the_validation})
        else:
          the_matrix, the_validation = view_logic.validate_download_form(the_matrix, request.POST)
          if the_validation:
            client_address = title = clicky_cookie = intercom_id = ''
            if 'hubspotutk' in request.COOKIES:
              the_cookie = request.COOKIES['hubspotutk']
            else:
              the_cookie = None
            if 'HTTP_REFERER' in request.META:
              the_ref = request.META['HTTP_REFERER']
            else:
              the_ref = None
            if 'REMOTE_ADDR' in request.META:
              client_address = request.META['REMOTE_ADDR']
            if 'title' in request.POST:
              title = request.POST['title']
            if '_jsuid' in request.COOKIES:
              clicky_cookie = request.COOKIES['_jsuid']
            if 'intercom-id' in request.COOKIES:
              intercom_id = request.COOKIES['intercom-id']
            the_type = 'download'
            if 'type' in request.POST and request.POST['type'] == 'demo':
              the_type = 'demo'
            if the_type == 'download':
              download_uuid = str(uuid.uuid1())
              dwnld = DownloadModel.objects.create(name=the_matrix['name'],
                                                   email=the_matrix['email'],
                                                   I_agree_to_EULA=True,
                                                   ip_address=client_address,
                                                   download_uuid=download_uuid,
                                                   clicky_cookie=clicky_cookie,
                                                   intercom_id=intercom_id)
              subject = 'Download'
              message2 = """
Download Form

Name: %s
Sender: %s
Client IP: %s
""" % (the_matrix['name'], the_matrix['email'], client_address)
              from_address = 'support@device42.com'
              recipients = ['raj@rajlog.com', ]
              if settings.DEBUG:
                recipients = ['dave.amato@device42.com', ]
              view_logic.immediate_download_send(request, the_matrix['name'], the_matrix['email'], download_uuid)
              view_logic.hubspot_data_send(title, the_cookie, client_address, the_ref, the_matrix['name'],
                                           the_matrix['email'], the_matrix['vp'])

            else:
              ScheduleModel.objects.create(name=the_matrix['name'],
                                           email=the_matrix['email'],
                                           ip_address=client_address,
                                           clicky_cookie=clicky_cookie,
                                           intercom_id=intercom_id)
              message2 = """
Download Form

Name: %s
Sender: %s
Client IP: %s
""" % (the_matrix['name'], the_matrix['email'], client_address)
              from_address = 'support@device42.com'
              recipients = ['scanelli@device42.com', 'al.rossini@device42.com', ]  # 'raj@rajlog.com',
              if settings.DEBUG:
                recipients = ['dave.amato@device42.com', ]
              subject = "FYI: online demo - already sent an invite "

              send_mail(subject, message2, from_address, recipients)
              view_logic.immediate_schedule_demo_send(the_matrix['name'], the_matrix['email'])
              view_logic.hubspot_data_send(title, the_cookie, client_address, the_ref, the_matrix['name'],
                                           the_matrix['email'], the_matrix['vp'], None, None, None, 'demo')
          else:
            # print 'download form filled - errors', request.POST, request.META
            return Response(500, content={'code': 0, 'msg': the_matrix, 'validation': the_validation})
      else:
        recipients = ['raj@rajlog.com', ]
        if settings.DEBUG:
          recipients = ['dave.amato@device42.com']
        send_mail('download -ve', str(request.POST), 'support@device42.com', recipients)
    else:
      recipients = ['raj@rajlog.com', ]
      if settings.DEBUG:
        recipients = ['dave.amato@device42.com', ]
      send_mail('download -ve', str(request.POST), 'support@device42.com', recipients)
    request.session['temp_data'] = the_matrix
    return Response(200, content={'code': 0, 'msg': 'done'})


class HubSpotFormFill(View):
  permissions = (AllowAny,)

  def post(self, request):
    print request, self
    return Response(200, content={'done'})

@never_cache
def solutions_bmc_remedy(request):
  form = forms.TryDownloadsForm()
  if request.method == 'POST':
    the_ref = client_address = clicky_cookie = intercom_id = the_cookie = request_cookies = ''
    if 'HTTP_REFERER' in request.META:
      the_ref = request.META['HTTP_REFERER']
    else:
      the_ref = None
    if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
    if 'hubspotutk' in request.COOKIES: the_cookie = request.COOKIES['hubspotutk']
    if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
    if 'intercom-id' in request.COOKIES:
      intercom_id = request.COOKIES['intercom-id']
    request_cookies = request.COOKIES

    if request.POST['flag'] == 'download':
        link = view_logic.generate_link_generic('d42-bmc_v1.1.zip')
        return HttpResponseRedirect(link)
    else:
      form = forms.TryDownloadsForm(request.POST)
      if form.is_valid():
        download_uuid = str(uuid.uuid1())
        email_clean = form.cleaned_data['email']
        name_clean = form.cleaned_data['name']
        dwnld = models.DownloadModel.objects.create(
          name=name_clean,
          email=email_clean,
          I_agree_to_EULA=True,
          ip_address=client_address,
          download_uuid=download_uuid,
          clicky_cookie=clicky_cookie,
          request_cookies=request_cookies
        )
        subject = 'Download'
        message2 = """
                                  Download Form Submission

                                  Name: %s
                                  Sender: %s
                                  Client IP: %s
                                  """ % (name_clean, email_clean, client_address)

        from_address = 'support@device42.com'
        recipients = ['raj@rajlog.com']
        if settings.DEBUG:
          recipients = ['dave.amato@device42.com', ]
        view_logic.immediate_download_send(request, name_clean, email_clean, download_uuid)
        send_mail(subject, message2, from_address, recipients)
        view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean,
                                     email_clean, '')
        request.session['temp_data'] = form.cleaned_data
        return redirect('thanks', id=1)

  return render(request, 'landing/Device42-Bmc-Remedy.html', {'form': form})

@never_cache
def solutions_jira(request):
  form = forms.TryDownloadsForm()
  if request.method == 'POST':
    the_ref = client_address = clicky_cookie = intercom_id = the_cookie = request_cookies = ''
    if 'HTTP_REFERER' in request.META:
      the_ref = request.META['HTTP_REFERER']
    else:
      the_ref = None
    if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
    if 'hubspotutk' in request.COOKIES: the_cookie = request.COOKIES['hubspotutk']
    if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
    if 'intercom-id' in request.COOKIES:
      intercom_id = request.COOKIES['intercom-id']
    request_cookies = request.COOKIES

    form = forms.TryDownloadsForm(request.POST)
    if form.is_valid():
      download_uuid = str(uuid.uuid1())
      email_clean = form.cleaned_data['email']
      name_clean = form.cleaned_data['name']
      dwnld = models.DownloadModel.objects.create(
        name=name_clean,
        email=email_clean,
        I_agree_to_EULA=True,
        ip_address=client_address,
        download_uuid=download_uuid,
        clicky_cookie=clicky_cookie,
        request_cookies=request_cookies
      )
      subject = 'Download'
      message2 = """
                                Download Form Submission

                                Name: %s
                                Sender: %s
                                Client IP: %s
                                """ % (name_clean, email_clean, client_address)

      from_address = 'support@device42.com'
      recipients = ['raj@rajlog.com']
      if settings.DEBUG:
        recipients = ['dave.amato@device42.com', ]
      view_logic.immediate_download_send(request, name_clean, email_clean, download_uuid)
      send_mail(subject, message2, from_address, recipients)
      view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean,
                                   email_clean, '')
      request.session['temp_data'] = form.cleaned_data
      return redirect('thanks', id=1)

  return render(request, 'landing/Device42-Jira.html', {'form': form})

@never_cache
def solutions_zendesk(request):
  form = forms.TryDownloadsForm()
  if request.method == 'POST':
    the_ref = client_address = clicky_cookie = intercom_id = the_cookie = request_cookies = ''
    if 'HTTP_REFERER' in request.META:
      the_ref = request.META['HTTP_REFERER']
    else:
      the_ref = None
    if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
    if 'hubspotutk' in request.COOKIES: the_cookie = request.COOKIES['hubspotutk']
    if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
    if 'intercom-id' in request.COOKIES:
      intercom_id = request.COOKIES['intercom-id']
    request_cookies = request.COOKIES

    form = forms.TryDownloadsForm(request.POST)
    if form.is_valid():
      download_uuid = str(uuid.uuid1())
      email_clean = form.cleaned_data['email']
      name_clean = form.cleaned_data['name']
      dwnld = models.DownloadModel.objects.create(
        name=name_clean,
        email=email_clean,
        I_agree_to_EULA=True,
        ip_address=client_address,
        download_uuid=download_uuid,
        clicky_cookie=clicky_cookie,
        request_cookies=request_cookies
      )
      subject = 'Download'
      message2 = """
                            Download Form Submission

                            Name: %s
                            Sender: %s
                            Client IP: %s
                            """ % (name_clean, email_clean, client_address)

      from_address = 'support@device42.com'
      recipients = ['raj@rajlog.com']
      if settings.DEBUG:
        recipients = ['dave.amato@device42.com', ]
      view_logic.immediate_download_send(request, name_clean, email_clean, download_uuid)
      send_mail(subject, message2, from_address, recipients)
      view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean,
                                   email_clean, '')
      request.session['temp_data'] = form.cleaned_data
      return redirect('thanks', id=1)

  return render(request, 'landing/Device42-Zendesk.html', {'form': form})


@never_cache
def solutions_samanage(request):
  form = forms.TryDownloadsForm()
  if request.method == 'POST':
    the_ref = client_address = clicky_cookie = intercom_id = the_cookie = request_cookies = ''
    if 'HTTP_REFERER' in request.META:
      the_ref = request.META['HTTP_REFERER']
    else:
      the_ref = None
    if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
    if 'hubspotutk' in request.COOKIES: the_cookie = request.COOKIES['hubspotutk']
    if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
    if 'intercom-id' in request.COOKIES:
      intercom_id = request.COOKIES['intercom-id']
    request_cookies = request.COOKIES

    form = forms.TryDownloadsForm(request.POST)
    if form.is_valid():
      download_uuid = str(uuid.uuid1())
      email_clean = form.cleaned_data['email']
      name_clean = form.cleaned_data['name']
      dwnld = models.DownloadModel.objects.create(
        name=name_clean,
        email=email_clean,
        I_agree_to_EULA=True,
        ip_address=client_address,
        download_uuid=download_uuid,
        clicky_cookie=clicky_cookie,
        request_cookies=request_cookies
      )
      subject = 'Download'
      message2 = """
                            Download Form Submission

                            Name: %s
                            Sender: %s
                            Client IP: %s
                            """ % (name_clean, email_clean, client_address)

      from_address = 'support@device42.com'
      recipients = ['raj@rajlog.com']
      if settings.DEBUG:
        recipients = ['dave.amato@device42.com', ]
      view_logic.immediate_download_send(request, name_clean, email_clean, download_uuid)
      send_mail(subject, message2, from_address, recipients)
      view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean,
                                   email_clean, '')
      request.session['temp_data'] = form.cleaned_data
      return redirect('thanks', id=1)

  return render(request, 'landing/Device42-Samanage.html', {'form': form})


@never_cache
def solutions_hpsm(request):
  form = forms.TryDownloadsForm()
  if request.method == 'POST':
    the_ref = client_address = clicky_cookie = intercom_id = the_cookie = request_cookies = ''
    if 'HTTP_REFERER' in request.META:
      the_ref = request.META['HTTP_REFERER']
    else:
      the_ref = None
    if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
    if 'hubspotutk' in request.COOKIES: the_cookie = request.COOKIES['hubspotutk']
    if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
    if 'intercom-id' in request.COOKIES:
      intercom_id = request.COOKIES['intercom-id']
    request_cookies = request.COOKIES

    form = forms.TryDownloadsForm(request.POST)
    if form.is_valid():
      download_uuid = str(uuid.uuid1())
      email_clean = form.cleaned_data['email']
      name_clean = form.cleaned_data['name']
      dwnld = models.DownloadModel.objects.create(
        name=name_clean,
        email=email_clean,
        I_agree_to_EULA=True,
        ip_address=client_address,
        download_uuid=download_uuid,
        clicky_cookie=clicky_cookie,
        request_cookies=request_cookies
      )
      subject = 'Download'
      message2 = """
                        Download Form Submission

                        Name: %s
                        Sender: %s
                        Client IP: %s
                        """ % (name_clean, email_clean, client_address)

      from_address = 'support@device42.com'
      recipients = ['raj@rajlog.com']
      if settings.DEBUG:
        recipients = ['dave.amato@device42.com', ]
      view_logic.immediate_download_send(request, name_clean, email_clean, download_uuid)
      send_mail(subject, message2, from_address, recipients)
      view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean,
                                   email_clean, '')
      request.session['temp_data'] = form.cleaned_data
      return redirect('thanks', id=1)

  return render(request, 'landing/Device42-Hpsm.html', {'form': form})

@never_cache
def solutions_service_now(request):
  form = forms.TryDownloadsForm()
  if request.method == 'POST':
    the_ref = client_address = clicky_cookie = intercom_id = the_cookie = request_cookies = ''
    if 'HTTP_REFERER' in request.META:
      the_ref = request.META['HTTP_REFERER']
    else:
      the_ref = None
    if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
    if 'hubspotutk' in request.COOKIES: the_cookie = request.COOKIES['hubspotutk']
    if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
    if 'intercom-id' in request.COOKIES:
      intercom_id = request.COOKIES['intercom-id']
    request_cookies = request.COOKIES

    if request.POST['flag'] == 'download':
        link = "https://api.github.com/repos/device42/servicenow_device42_mapping/zipball"
        return HttpResponseRedirect(link)
    else:
      form = forms.TryDownloadsForm(request.POST)
      if form.is_valid():
        download_uuid = str(uuid.uuid1())
        email_clean = form.cleaned_data['email']
        name_clean = form.cleaned_data['name']
        dwnld = models.DownloadModel.objects.create(
          name=name_clean,
          email=email_clean,
          I_agree_to_EULA=True,
          ip_address=client_address,
          download_uuid=download_uuid,
          clicky_cookie=clicky_cookie,
          request_cookies=request_cookies
        )
        subject = 'Download'
        message2 = """
                    Download Form Submission

                    Name: %s
                    Sender: %s
                    Client IP: %s
                    """ % (name_clean, email_clean, client_address)

        from_address = 'support@device42.com'
        recipients = ['raj@rajlog.com']
        if settings.DEBUG:
          recipients = ['dave.amato@device42.com', ]
        view_logic.immediate_download_send(request, name_clean, email_clean, download_uuid)
        send_mail(subject, message2, from_address, recipients)
        view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean,
                                     email_clean, '')
        request.session['temp_data'] = form.cleaned_data
        return redirect('thanks', id=1)

  return render(request, 'landing/Device42-Service-Now.html', {'form': form})


@never_cache
def solutions_servicenow_express(request):
  form = forms.TryDownloadsForm()
  if request.method == 'POST':
    the_ref = client_address = clicky_cookie = intercom_id = the_cookie = request_cookies = ''
    if 'HTTP_REFERER' in request.META:
      the_ref = request.META['HTTP_REFERER']
    else:
      the_ref = None
    if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
    if 'hubspotutk' in request.COOKIES: the_cookie = request.COOKIES['hubspotutk']
    if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
    if 'intercom-id' in request.COOKIES:
      intercom_id = request.COOKIES['intercom-id']
    request_cookies = request.COOKIES

    if request.POST['flag'] == 'download':
        link = "https://api.github.com/repos/device42/device42_to_servicenow_express/zipball"
        return HttpResponseRedirect(link)
    else:
      form = forms.TryDownloadsForm(request.POST)
      if form.is_valid():
        download_uuid = str(uuid.uuid1())
        email_clean = form.cleaned_data['email']
        name_clean = form.cleaned_data['name']
        dwnld = models.DownloadModel.objects.create(
          name=name_clean,
          email=email_clean,
          I_agree_to_EULA=True,
          ip_address=client_address,
          download_uuid=download_uuid,
          clicky_cookie=clicky_cookie,
          request_cookies=request_cookies
        )
        subject = 'Download'
        message2 = """
              Download Form Submission

              Name: %s
              Sender: %s
              Client IP: %s
              """ % (name_clean, email_clean, client_address)

        from_address = 'support@device42.com'
        recipients = ['raj@rajlog.com']
        if settings.DEBUG:
          recipients = ['dave.amato@device42.com', ]
        view_logic.immediate_download_send(request, name_clean, email_clean, download_uuid)
        send_mail(subject, message2, from_address, recipients)
        view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean,
                                     email_clean, '')
        request.session['temp_data'] = form.cleaned_data
        return redirect('thanks', id=1)

  return render(request, 'landing/Device42-Servicenow-Express.html', {'form': form})

def solutions_generator(request, slug):
  the_ref = request.META.get('HTTP_REFERER', None)
  form = None
  if request.method == 'POST':
    the_ref = client_address = clicky_cookie = intercom_id = the_cookie = request_cookies = ''
    if 'HTTP_REFERER' in request.META: the_ref = request.META['HTTP_REFERER']
    else: the_ref = None
    if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
    if 'hubspotutk' in request.COOKIES: the_cookie = request.COOKIES['hubspotutk']
    if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
    if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']
    request_cookies = request.COOKIES

    form = forms.LandingDownloadForm(request.POST)
    if form.is_valid():
      if request.POST['action'] == 'schedule':
        name = form.cleaned_data['name']
        sender = form.cleaned_data['email']

        message2 = """
          Name: %s
          Email: %s
          IP: %s
          """ % (name, sender, client_address)
        from_address = ['support@device42.com']
        recipients = ['scanelli@device42.com', 'al.rossini@device42.com', ]  # 'raj@rajlog.com',
        if settings.DEBUG:
          recipients = ['dave.amato@device42.com', ]
        subject = "FYI: online demo - already sent an invite "

        send_mail(subject, message2, from_address, recipients)
        if not settings.DEBUG:
          view_logic.immediate_schedule_demo_send(name, sender)
          view_logic.hubspot_data_send('schedule_demo', the_cookie, client_address, the_ref, form.cleaned_data['name'],
                                       form.cleaned_data['email'], None, None, None, '')
        request.session['temp_data'] = form.cleaned_data
        return redirect('thanks', id=0)
      elif request.POST['action'] == 'download':
        if request.POST['instance_type'] == 'On-prem':
          if request.POST['main'] == '':
            download_uuid = str(uuid.uuid1())
            email_clean = form.cleaned_data['email']
            name_clean = form.cleaned_data['name']
            dwnld = models.DownloadModel.objects.create(
              name=name_clean,
              email=email_clean,
              I_agree_to_EULA=True,
              ip_address=client_address,
              download_uuid=download_uuid,
              clicky_cookie=clicky_cookie,
              request_cookies=request_cookies
            )
            subject = 'Download'
            message2 = """
            Download Form Submission
    
            Name: %s
            Sender: %s
            Client IP: %s
            """ % (name_clean, email_clean, client_address)

            from_address = 'support@device42.com'
            recipients = ['raj@rajlog.com']
            if settings.DEBUG: recipients = ['dave.amato@device42.com', ]
            view_logic.immediate_download_send(request, name_clean, email_clean, download_uuid)
            send_mail(subject, message2, from_address, recipients)
            view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean,
                                         email_clean, '')
            request.session['temp_data'] = form.cleaned_data
            return redirect('thanks', id=1)
          else:
            send_mail('download -ve', str(request.POST), 'support@device42.com', ['raj@rajlog.com'])
            return redirect('thanks', id=9)
        elif request.POST['instance_type'] == 'Cloud':
          if request.POST['main'] == '':
            email_clean = form.cleaned_data['email']
            try:
              cloud_record = models.CloudModel.objects.get(email=email_clean, cloud_url__isnull=False)
            except MultipleObjectsReturned:
              cloud_record = models.CloudModel.objects.filter(email=email_clean, cloud_url__isnull=False).first()
            except ObjectDoesNotExist:
              cloud_record = None

            if not cloud_record:
              try:
                o = OneTimeSecret(settings.OTS_EMAIL, settings.OTS_APIKEY)
                secret = o.share(form.cleaned_data['cloud_password'])
                cloud_password = secret["secret_key"]
              except:
                cloud_password = '__plain__' + str(form.cleaned_data['cloud_password'])

              name_clean = form.cleaned_data['name']
              activation_uuid = str(uuid.uuid1())

              cloud_record = models.CloudModel.objects.create(
                name=name_clean,
                email=email_clean,
                cloud_password=cloud_password,
                ip_address=client_address,
                clicky_cookie=clicky_cookie,
                activation_uuid=activation_uuid,
                request_cookies=request_cookies
              )

              cloud_record.cloud_url = 'https://d42-%s.device42.net/' % format(cloud_record.id, '04')
              cloud_record.save()

              subject = 'Download'
              message2 = """
              Cloud Form Submission
    
              Name: %s
              Sender: %s
              Cloud Url: %s
              Client IP: %s
              Activated : False
              """ % (name_clean, email_clean, cloud_record.cloud_url, cloud_record.ip_address)

              from_address = 'support@device42.com'
              recipients = ['raj@rajlog.com']
              if settings.DEBUG:
                recipients = ['dave.amato@device42.com', ]
              view_logic.immediate_cloud_activation_send(request, name_clean, email_clean, activation_uuid)
              send_mail(subject, message2, from_address, recipients)
              view_logic.hubspot_data_send('download', the_cookie, client_address, the_ref, name_clean, email_clean, '', None, None, None, None, True)
              request.session['temp_data'] = form.cleaned_data
              return redirect('thanks', id=12)
            else:
              if not cloud_record.active:
                form.add_error('email', mark_safe('''This email already initialized cloud instance.<br>
                                                     But instance not activated, we resend link, please check email.'''))
                view_logic.immediate_cloud_activation_send(request, cloud_record.name, cloud_record.email, cloud_record.activation_uuid)
              else:
                form.add_error('email', mark_safe('''This email has already initialized a Cloud based instance.<br>
                                                  Go to <a href="%s">%s</a> and login with your existing credentials.''' % (cloud_record.cloud_url, cloud_record.cloud_url)))
  else:
    form = forms.LandingDownloadForm()

  if slug in LANDING_DATA:
    if 'template' in LANDING_DATA[slug]:
      return render(request, LANDING_DATA[slug]['template'], { 'page': LANDING_DATA[slug], 'form': form})
    else:
      return render(request, 'landing_alt/layout-1.html', { 'page': LANDING_DATA[slug]})
  else:
    raise Http404

@never_cache
def free_tools_doc_template(request):
  form = None
  if request.method == 'POST':
    form = forms.OtherDownloadsForm(request.POST)

    if form.is_valid():
      client_address = clicky_cookie = intercom_id = ''
      fc = form.save(commit=False)
      if 'REMOTE_ADDR' in request.META: client_address = request.META['REMOTE_ADDR']
      if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
      if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']

      fc.ip_address = client_address
      fc.clicky_cookie = clicky_cookie
      fc.intercom_id = intercom_id
      fc.type = 'spreadsheet_template'
      fc.name = name = form.cleaned_data['name']
      fc.email = to_email = form.cleaned_data['email']
      fc.ip_address = client_address
      fc.save()

      from_email = 'support@device42.com'
      subject = 'Download'
      text = '''
            Hi %s,

            Attached, please find the spreadsheet you requested, and thank you for your interest in Device42!
            If you aren't currently a Device42 user, give it a try for free! Download here: https://docs.google.com/spreadsheets/d/1Ae7weoKUqVIFoPg-ybgB6addjerc48zpPE8lnmswoxI/edit?usp=sharing

            Regards,


            The Device42 Team
            ''' % name

      html = '''
            <p>Hi %s,</p>

            <p>Attached, please find the spreadsheet you requested, and thank you for your interest in Device42!<br>If you aren't currently a Device42 user, give it a try for free! Download <a href="https://docs.google.com/spreadsheets/d/1Ae7weoKUqVIFoPg-ybgB6addjerc48zpPE8lnmswoxI/edit?usp=sharing" target="_blank">here</a>.</p>

            <p>Regards,</p><br>
            <p>The Device42 Team</p>
            ''' % name

      view_logic.send_mailgun_message(
        from_email, to_email, subject, text, html)

      request.session['temp_data'] = form.cleaned_data
      return thanks(request, id='14')
    else:
      return render(request, 'forms/free_tools/dc_doc_template.html', {'form': form})
  else:
    form = forms.OtherDownloadsForm()

  return render(request, 'forms/free_tools/dc_doc_template.html', {'form': form})

def free_tools_doc_template_dl(request):
  return render(request, 'forms/free_tools/dc_doc_template_dl.html')

def dl_idc_emc_wp(request):
  return render(request, 'landing/Device42-dl-idc-emc-wp.html')

def cookies(request):
  return render(request, 'cookies.html')

def webinar_videos(request):
  return render(request, 'webinar_videos.html')

