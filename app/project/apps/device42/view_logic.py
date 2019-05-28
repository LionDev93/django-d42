import base64
import hashlib
import hmac
import json
import os
import requests
import sys
import time
import traceback
import urllib
import user_agents
from datetime import datetime, timedelta

from IPy import IP
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _

import project
from project.apps.device42 import incognitos
from project.apps.device42.models import GeoIPDB, OtherDownloads, CurrentCustomers


def encode(aws_secret_access_key, str, urlencode=False):
  b64_hmac = base64.encodestring(hmac.new(aws_secret_access_key, str, hashlib.sha1).digest()).strip()
  if urlencode:
    return urllib.quote_plus(b64_hmac)
  else:
    return b64_hmac


def query_args_hash_to_string(query_args):
  pairs = []
  for k, v in query_args.items():
    piece = k
    if v is not None:
      piece += "=%s" % urllib.quote_plus(str(v))
    pairs.append(piece)

  return '&'.join(pairs)


def validate_download_form(the_matrix, args):
  the_matrix['name'] = args['name']
  the_matrix['email'] = args['email']

  if args['name'] != '' and args['email'] != '':
    if get_validate(args['email']):
      return the_matrix, True
    else:
      the_matrix['email_error'] = True
      return the_matrix, False
  else:
    if args['name'] == '':
      the_matrix['name_error'] = True
    if args['email'] == '':
      the_matrix['email_error'] = True
    return the_matrix, False


def generate_download_links(expires):
  import boto
  key_pair_id = "APKAJ3OPRB6IA4TA23CA"
  priv_key_filename = "pk-APKAJ3OPRB6IA4TA23CA.pem"
  priv_key_file = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))),
    'credentials', priv_key_filename)

  cf = boto.connect_cloudfront()
  dist = cf.get_distribution_info('E111F17TJ5VJRY')

  link_names = [
    {'name': 'VMware/Oracle Virtual Box ', 'link': 'https://d17xs64pqeg3rv.cloudfront.net/Device42-15.15.00-ovf.7z',
     'size': '3.1 GB',
     'img_src': 'http://d42i.s3.amazonaws.com/media/images/links/vmware.png'},
    {'name': 'Citrix Xenserver', 'link': 'https://d17xs64pqeg3rv.cloudfront.net/Device42-15.15.00-xva.7z',
     'size': '3.1 GB',
     'img_src': "http://d42i.s3.amazonaws.com/media/images/links/citrix_xen.png"},
    {'name': 'Microsoft HyperV', 'link': 'https://d17xs64pqeg3rv.cloudfront.net/Device42-15.15.00-vhd.7z',
     'size': '4.0 GB',
     'img_src': "http://d42i.s3.amazonaws.com/media/images/links/hyperv.png"},
    {'name': 'Xen/OpenStack/KVM', 'link': 'https://d17xs64pqeg3rv.cloudfront.net/Device42-15.15.00-qcow2.7z',
     'size': '3.4 GB',
     'img_src': "http://d42i.s3.amazonaws.com/media/images/links/kvm_qemu_raw.png"},
  ]

  download_links = []
  for _dict in link_names:
    http_signed_url = dist.create_signed_url(_dict['link'], key_pair_id, expires, private_key_file=priv_key_file)
    download_links.append(
      {'name': _dict['name'], 'link': http_signed_url, 'size': _dict['size'], 'img_src': _dict['img_src']})
  return download_links


def generate_link_generic(path, storage_bucket='d42-auto-discover'):
  expires = int(time.time() + 172800)
  query_args = {}
  canonical_str = str(expires)
  storage_url = 'https://s3.amazonaws.com'

  if 'OpenDisc' in path: storage_bucket = 'd42-open-discover'
  # string_to_sign = "GET\n\n\n" + canonical_str + "\n" + "/d42-auto-discover/%s" % path
  string_to_sign = "GET\n\n\n" + canonical_str + "\n" + "/%s/%s" % (storage_bucket, path)
  # url = 'https://s3.amazonaws.com/d42-auto-discover/%s' % path
  url = '%s/%s/%s' % (storage_url, storage_bucket, path)
  encoded_canonical = encode('kOvhzMuq/yuXdxyjhYa7dk6XfXWsI1Q+JaQ0Lkm9', string_to_sign)
  # url += "/%s" % urllib.quote_plus('kOvhzMuq/yuXdxyjhYa7dk6XfXWsI1Q+JaQ0Lkm9')
  query_args['Signature'] = encoded_canonical
  query_args['Expires'] = expires
  query_args['AWSAccessKeyId'] = 'AKIAIS2U7NVNTQXL7AMQ'
  url += "?%s&FixForIE=.exe" % query_args_hash_to_string(query_args)
  return url


def generate_link_software(package, request, form=None):
  from django.core.urlresolvers import resolve
  download = request.POST.get('download')
  if package in project.views._getUtilities().values():
    url = client_address = clicky_cookie = intercom_id = ''
    the_cookie = the_ref = None
    update_type = 'regular'

    try:
      client_address = request.META['HTTP_X_FORWARDED_FOR']
    except:
      client_address = request.META['REMOTE_ADDR']

    if 'HTTP_REFERER' in request.META: the_ref = request.META['HTTP_REFERER']
    if '_jsuid' in request.COOKIES: clicky_cookie = request.COOKIES['_jsuid']
    if 'hubspotutk' in request.COOKIES: the_cookie = request.COOKIES['hubspotutk']
    if 'intercom-id' in request.COOKIES: intercom_id = request.COOKIES['intercom-id']
    if package != "update": OtherDownloads.objects.create(type=('%s' % download), ip_address=client_address,
                                                          clicky_cookie=clicky_cookie, intercom_id=intercom_id)
    if form is not None:
      fc = form.save(commit=False)

    if package == "opendiscovery":
      if download == "open disc msi":
        url = generate_link_generic('D42OpenDiscv202.msi')
      if download == "open disc bin":
        url = generate_link_generic('D42OpenDiscv202.zip')
    elif package == "autodiscovery":
      if download == ".net auto disc tool":
        url = generate_link_generic('D42AutoDisc_v1470.exe')
      elif download == "linux auto disc tool":
        url = generate_link_generic('d42_linux_autodisc_v6_7_12.zip')
      elif download == ".net ping sweep":
        url = generate_link_generic('d42_pingsweep_v3.5.2.zip')
      elif download == "netflow":
        url = generate_link_generic('d42-netflow-collector-v200.zip')
      elif download == "rc":
        url = generate_link_generic('D42-RC-15.00.00-ovf.zip', 'device42')
      elif download == "wds":
        url = generate_link_generic('Device42Discovery_15_14_03.msi', 'device42')
    elif package == "miscellaneous-tools":
      if download == "d42 print utility":
        url = generate_link_generic('D42PrintInstaller_v1.0.4.msi')
      if download == "d42 agent uploadtool":
        url = generate_link_generic('d42_uploadtool.zip', 'device42')
      if download == "D42 ODBC driver":
        url = generate_link_generic('D42_ODBC_v1.0.zip', 'device42')
    elif package == "bulk-data-management":
      if download == "generic import tool":
        url = generate_link_generic('d42_generic_import_tool_v7.3.0.exe')
    elif package == "update":
      if download == "update-regular" or download == "update-pma":
        if download == "update-pma":
          update_type = 'pma'
        elif ('update_type' in request.POST and 'beta' == request.POST.get('update_type')):
          update_type = 'beta'

        if form is not None:
          fc.update_type = update_type
          fc.ip_address = client_address
          fc.request_cookies = request.COOKIES
          fc.save()

        subject = 'update'
        sender = form.cleaned_data['email']
        message2 = 'Update Form: Sender: %s Client IP: %s Update Type: %s' % (sender, client_address, update_type)
        from_address = 'support@device42.com'
        recipients = ['scanelli@device42.com']
        if settings.DEBUG:
          recipients = ['dave.amato@device42.com']
        immediate_update_send(sender, message2, update_type)
        hubspot_data_send('update', the_cookie, client_address, the_ref, '', sender, None, message2)
        if form is not None:  request.session['temp_data'] = form.cleaned_data
        return '/thanks/2/'  # reverse('project.views.thanks', kwargs={'id': '2'})

    if form is not None:  request.session['temp_data'] = form.cleaned_data

  else:
    return resolve(request.path_info).url_name

  return url


def generate_power_link(platform):
  expires = int(time.time() + 259200)
  query_args = {}
  canonical_str = str(expires)
  if platform == 'vmware':
    string_to_sign = "GET\n\n\n" + canonical_str + "\n" + "/device42/D42_Power_Appliance_v1380-ovf.7z"
    url = 'https://s3.amazonaws.com/device42/D42_Power_Appliance_v1380-ovf.7z'
  elif platform == 'vmdk':
    string_to_sign = "GET\n\n\n" + canonical_str + "\n" + "/device42/D42_Power_Appliance_v1380-vmdk.7z"
    url = 'https://s3.amazonaws.com/device42/D42_Power_Appliance_v1380-vmdk.7z'
  elif platform == 'xen':
    string_to_sign = "GET\n\n\n" + canonical_str + "\n" + "/device42/D42_Power_Appliance_v1380-xva.7z"
    url = 'https://s3.amazonaws.com/device42/D42_Power_Appliance_v1380-xva.7z'
  elif platform == 'vhd':
    string_to_sign = "GET\n\n\n" + canonical_str + "\n" + "/device42/D42_Power_Appliance_v1380-vhd.7z"
    url = 'https://s3.amazonaws.com/device42/D42_Power_Appliance_v1380-vhd.7z'
  else:
    string_to_sign = "GET\n\n\n" + canonical_str + "\n" + "/device42/D42_Power_Appliance_v1380.img.bz2"
    url = 'https://s3.amazonaws.com/device42/D42_Power_Appliance_v1380.img.bz2'
  encoded_canonical = encode('kOvhzMuq/yuXdxyjhYa7dk6XfXWsI1Q+JaQ0Lkm9', string_to_sign)
  query_args['Signature'] = encoded_canonical
  query_args['Expires'] = expires
  query_args['AWSAccessKeyId'] = 'AKIAIS2U7NVNTQXL7AMQ'
  url += "?%s" % query_args_hash_to_string(query_args)
  return url


def immediate_update_send(sender, message, update_type):  # , curver name
  recipients = ['raj@rajlog.com', 'jason.lomax@device42.com', ]
  # if settings.DEBUG: recipients = ['dave.amato@device42.com']
  # the_domain = sender.split('@')[1]
  # if the_domain.split('.')[0] not in ['gmail', 'yahoo', 'hotmail', 'me', 'mail','outlook']:
  if not get_validate(sender):
    text_content, html_content = text_html_calculate_updatelink(update_type)
    if update_type == 'pma':
      subject = _('Device42 Power Monitoring Appliance Update')
    elif update_type == 'beta':
      subject = _('Device42 Beta')
    else:
      subject = _('Device42 Update')
    send_mailgun_message("Device42 Support Team <support@corp.device42.com>", sender, subject, text_content,
                         html_content)

    send_mail('update', message, 'support@device42.com', recipients)
  else:
    send_mail('update not emailed', message, 'support@device42.com', recipients)


def text_html_calculate_updatelink(update_type):
  beta_notes_txt=''
  beta_notes_html=''

  if update_type == 'pma':
    link = generate_link_generic('update-power-13.8.0.1503518578.zip.enc', 'device42')
    release_notes = 'https://blog.device42.com/tag/power-appliance/'
  elif update_type == 'beta':
    link = generate_link_generic('update-150000-to-15.14.01.BETA.zip.enc', 'device42')
    release_notes = 'https://blog.device42.com/tag/release/'

    beta_notes_raw = _("""%sThe following update is a beta release with our upcoming changes to Discovery Dashboard and Quality Scores. This release should only be used in a non-production server and upgrades from this beta will not be supported. We strongly recommend taking a snapshot on your hypervisor before applying this update!%s

      %sIn addition, you will need to update your Windows Discovery Service (WDS) installations to take advantage of our latest changes.  %s
      %sDownload the latest Windows Discovery Service (WDS) install %s%s
      """)
    wds_beta_link = generate_link_generic('Device42Discovery_15_14_01_BETA.msi', 'device42')
    wds_beta_link_html = "<a href='%s'>here</a>" % wds_beta_link
    beta_notes_html = beta_notes_raw % ('<p><strong>', '</strong></p>', '<p><strong>', '</strong></p>', '<p>', wds_beta_link_html, '</p>')
    beta_notes_txt = beta_notes_raw % ('', '', '', '', '', wds_beta_link, '')
  else:
    link = generate_link_generic('update-150000-to-15.15.01.1553860812.zip.enc', 'device42')
    release_notes = 'https://blog.device42.com/tag/release/'


  textmessage = _("""
  Hi,

  Please click below to download the Device42 update you recently requested. This link is valid for the 72 hours.

  Download update:  %s
  
  %s
  
  Instruction on how to upgrade can be found at:  https://device42.zendesk.com/entries/21783332

  Read about the latest release here:  %s

  Please reply to this email if you have issues applying the update.

  Regards,
  Device42 Support Team.
  """) % (link, beta_notes_txt, release_notes)

  htmlmessage = _("""
  <html><head></head><body>
  Hi,
  <p>Please <a href='%s'>click here</a> to download the Device42 update you recently requested.   This link is valid for the next 72 hours.</p>
  %s
  <p>For instructions on how to apply the update, <a href="https://device42.zendesk.com/entries/21783332">go here</a>.</p>
  <p>Read about the latest release notes <a href="%s">here</a>.</p>

  <p>Please reply to this email if you have issues applying the update. </p>

  Regards,<br>Device42 Support Team.
  </body></html>""") % (link, beta_notes_html, release_notes)

  return textmessage, htmlmessage


def send_mailgun_message(from_email, to_email, the_subject, text, html, bcc=None, attached_files=[]):  # ,
  if to_email.split('@')[1] in ['mail.ru', 'mailinator.com', ]: return -1  # todo out - take care in incognito check
  try:
    mail_post = requests.post(
      "https://api.mailgun.net/v2/corp.device42.com/messages",
      auth=("api", "key-08k09z9jf7jyte7vi22nozc-bgk7g-s2"),
      files=attached_files,
      data={"from": from_email,
            "to": to_email,
            "subject": the_subject,
            "text": text,
            "html": html,
            "v:my-custom-data": the_subject,
            "bcc": bcc
            })
    if mail_post.status_code != requests.codes.ok:
      print mail_post, mail_post.json()
      error_sending_msg(to_email, the_subject, text, html, from_email)
  except Exception as e:
    print 'error sending message', the_subject, to_email, str(e)
    error_sending_msg(to_email, the_subject, text, html, from_email)


def error_sending_msg(to_email, the_subject, text, html, from_email='support@device42.com'):
  from django.core.mail import EmailMessage, EmailMultiAlternatives
  receiveremail = ['raj@rajlog.com', ]
  if settings.DEBUG:
    receiveremail = ['dave.amato@device42.com', ]
  msg = EmailMessage('Device42 Message Send Error (via mailgun)', the_subject + ' ' + to_email, from_email,
                     receiveremail)
  msg.send()
  msg2 = EmailMultiAlternatives(the_subject, text, from_email, [to_email])
  msg2.attach_alternative(html, "text/html")
  msg2.send()

def hubspot_webinar_registration_data_send(the_method, the_cookie, client_address, the_ref, firstname, lastname, email, title):
  try:
    if the_method == "webinar_registration":
      the_data = {"firstname": firstname,
                  "lastname": lastname,
                  "email": email,
                  "title": title,
                  "hs_context": json.dumps({
                    "ipAddress": client_address,
                    "hutk": the_cookie,
                    "pageUrl": the_ref,
                    "pageName": the_method,
                    "goToWebinarWebinarKey": '5440942470098753794'
                  })
                  }
      form_id='c53d3e88-a234-4705-9abc-e9648b8167f1'
    elif the_method == "webinar2_registration":
      the_data = {"firstname": firstname,
                  "lastname": lastname,
                  "email": email,
                  "title": title,
                  "hs_context": json.dumps({
                    "ipAddress": client_address,
                    "hutk": the_cookie,
                    "pageUrl": the_ref,
                    "pageName": the_method,
                    "goToWebinarWebinarKey": '80159180703545601'
                  })
                  }
      form_id = 'f72c7c69-853f-44a5-a137-bc5a916a24ea'
    elif the_method == "webinar3_registration":
      the_data = {"firstname": firstname,
                  "lastname": lastname,
                  "email": email,
                  "title": title,
                  "hs_context": json.dumps({
                    "ipAddress": client_address,
                    "hutk": the_cookie,
                    "pageUrl": the_ref,
                    "pageName": the_method,
                    "goToWebinarWebinarKey": '6837847804968525569'
                  })
                  }
      form_id = '6cf29c0f-96ab-425a-8047-5262d38ec5d5'
    elif the_method == "second_webinar_registeration":
      the_data = {
                  "email": email,
                  "hs_context": json.dumps({
                    "ipAddress": client_address,
                    "hutk": the_cookie,
                    "pageUrl": the_ref,
                    "pageName": the_method,
                    "goToWebinarWebinarKey": '3096134971857316865'
                  })
                  }
      form_id = '2324a83d-c060-4708-89ac-02ce3e1625f6'

    the_url = "https://forms.hubspot.com/uploads/form/v2/433338/" + form_id

    hub_post = requests.post(
      the_url,
      data=the_data)
    if hub_post.status_code == 200:
      pass
    else:
      print 'failed hubspot', hub_post

  except Exception as e:
    print 'error sending hubspot data', firstname, email, str(e)

def hubspot_data_send(the_method, the_cookie, client_address, the_ref, name, email, topic=None, message=None,
                      phone=None, company=None, type=None, cloud=False):
  try:
    if ' ' in name:
      firstname = name.split(' ')[0]
      lastname = name.split(' ', 1)[1]
    else:
      firstname = name
      lastname = ''
    the_data = {"firstname": firstname,
                "lastname": lastname,
                "email": email,
                "hs_context": json.dumps({
                  "ipAddress": client_address,
                  "hutk": the_cookie,
                  "pageUrl": the_ref,
                  "pageName": the_method
                })
                }
    if cloud: the_data.update({'cloud_version': 'true'})
    if the_method == 'download':
      form_id = '590b7b91-57e2-4ffc-9acb-6b9a1c81731c/'
    elif the_method == 'update':
      form_id = '271cc1bd-1ca4-4e23-a764-8d209f79eefb/'
    elif the_method == 'contact':
      form_id = '45503623-2e8c-4368-b9ff-d0ce2501a568/'
      the_data.update({'phone': phone, 'topic': topic, 'message': message})
    elif the_method == 'schedule_demo' or type == 'demo':
      form_id = '991eed0a-179a-4091-808a-72b35453108a/'
      if phone: the_data.update({'phone': phone})
    else:
      form_id = '590b7b91-57e2-4ffc-9acb-6b9a1c81731c/'
    the_url = "https://forms.hubspot.com/uploads/form/v2/433338/" + form_id
    hub_post = requests.post(
      the_url,
      # auth=("api", "key-08k09z9jf7jyte7vi22nozc-bgk7g-s2"),
      data=the_data)
    if hub_post.status_code == 204:
      pass
    else:
      print 'failed hubspot', hub_post
      # error_sending_msg(from_email, to_email, the_subject, text, html)
  except Exception as e:
    print 'error sending hubspot data', name, email, str(e)


def get_validate(email):
  # temporary remove validation

  try:
    _email = email.split('@')[1]
    if _email not in incognitos.INCOGNITO_LIST:
      return False
    else:
      return True
  #     # mg_result = requests.get(
  #     #   "https://api.mailgun.net/v2/address/validate",
  #     #   auth=("api", "pubkey-8gjl8zluch9vjktwusqpfzjz438jil20"),
  #     #   params={"address": email}).json()
  #     # return mg_result["is_valid"]
  except:
    import re
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
      return False
    else:
      return True


def send_email(subject, message, sender, to_list):
  if subject and message and sender:
    try:
      send_mail(subject, message, sender, to_list)
    except BadHeaderError:
      return HttpResponse('Invalid header found.')
    return HttpResponseRedirect('/thanks/9/')
  else:
    return HttpResponse(_("Make sure all fields are entered and valid."))


def parse_user_agent(ua):
  parsed_ua = user_agents.parse(ua)
  return parsed_ua.is_bot


def get_ip_data(ipaddress):
  continent = country = ''
  if IP(ipaddress).iptype() == 'PUBLIC':
    if GeoIPDB.objects.filter(ip=ipaddress):
      ipobj = GeoIPDB.objects.filter(ip=ipaddress)[0]
      if ipobj.last_updated < datetime.now(ipobj.last_updated.tzinfo) - timedelta(days=180):  # cache for 180 days?
        continent, country = store_ip_data(ipaddress)
      else:
        continent = ipobj.continent
        country = ipobj.country
    else:
      continent, country = store_ip_data(ipaddress)
  return continent, country


def store_ip_data(ipaddress):
  try:
    import geoip2.webservice
    client = geoip2.webservice.Client(109451, 'YfeYya1KZ1AH')
    response = client.city(ipaddress)
    city = country = domain = org = subdivision = timezone = continent = latitude = longitude = ''
    try:
      city = response.city.name
    except:
      pass
    try:
      country = response.country.iso_code
    except:
      pass
    try:
      domain = response.traits.domain
    except:
      pass
    try:
      org = response.traits.organization
    except:
      pass
    try:
      subdivision = response.subdivisions.most_specific.name
    except:
      pass
    try:
      timezone = response.location.timezone
    except:
      pass
    try:
      continent = response.continent.code
    except:
      pass
    try:
      latitude = response.location.latitude
    except:
      pass
    try:
      longitude = response.location.longitude
    except:
      pass
    if GeoIPDB.objects.filter(ip=ipaddress):
      ipobj = GeoIPDB.objects.filter(ip=ipaddress)[0]
    else:
      ipobj = GeoIPDB(ip=ipaddress)
    ipobj.city = city
    ipobj.country = country
    ipobj.domain = domain
    ipobj.org = org
    ipobj.subdivision = subdivision
    ipobj.timezone = timezone,
    ipobj.continent = continent
    ipobj.latitude = latitude
    ipobj.longitude = longitude
    ipobj.full_clean()
    ipobj.save()
    return ipobj.continent, ipobj.country
  except:
    traceback.print_exc(file=sys.stdout)
    return ''


def immediate_download_send(request, name, sender, download_uuid):
  text_content, html_content = text_html_calculate_linkgenerate(request, name, download_uuid)
  send_mailgun_message("Device42 Support Team <support@corp.device42.com>", sender, "Device42 download", text_content, html_content)


def immediate_cloud_activation_send(request, name, sender, activation_uuid):
  text_content, html_content = text_html_calculate_activategenerate(request, name, activation_uuid)
  send_mailgun_message("Device42 Support Team <support@corp.device42.com>", sender, "Device42 Cloud Trial Email Confirmation", text_content, html_content)

def immediate_cloud_data_send(request, cloud_instance, ots_url):
  text_content, html_content = text_html_calculate_datagenerate(request, cloud_instance, ots_url)
  send_mailgun_message("Device42 Support Team <support@corp.device42.com>", cloud_instance.email, "Device42 Cloud Trial Ready", text_content, html_content)

def immediate_schedule_demo_send(name, sender):
  text_content, html_content = text_html_calculate_scheduledemo(name)
  send_mailgun_message("Device42 Support Team <support@corp.device42.com>", sender, "Device42 Online Demo",
                       text_content, html_content, "Raj <raj@rajlog.com>")


def immediate_power_send(sender, platform, platform_title):
  the_domain = sender.split('@')[1]

  if the_domain == 'device42.com':
    text_content, html_content = text_html_calculate_powerlink(platform, platform_title)
    send_mailgun_message("Device42 Support Team <support@corp.device42.com>", sender,
                         "Device42 Power Appliance Download", text_content, html_content)


def text_html_calculate_scheduledemo(first_name):
  text1 = _("Hi %s,\n") % first_name
  text2 = _("""

Thank you for your interest in Device42.

To schedule an individualized demo, just click the following link and select a time slot: https://d42demo.youcanbook.me/

If you are unable to use this link, please reply to this email with a few available time slots that work for you (and please include your time zone!).

We look forward to connect with you.

Sincerely,
Device42 Team
600 Saw Mill Rd, West Haven CT 06516
1-866-343-7242
PS: This email was automatically generated, but you can still reply to talk to an actual person :)
""")

  html1 = _("<html><head></head><body>Hi %s,") % first_name
  html2 = _("""<p>Thank you for your interest in Device42. </p>
<p>To schedule an individualized demo, just click the following link and select a time slot: <a href="https://d42demo.youcanbook.me/">https://d42demo.youcanbook.me/</a></p>

<p>If you are unable to use this link, please reply to this email with a few available time slots that work for you (and please include your time zone!).
</p><p>
We look forward to connect with you.</p>
<p>
Sincerely,<br />
Device42 Team<br />
600 Saw Mill Rd, West Haven CT 06516<br />
1-866-343-7242<br />
PS: This email was automatically generated, but you can still reply to talk to an actual person :)
</p>
</body></html>
""")
  html_content = html1 + html2
  text_content = text1 + text2
  return text_content, html_content


def text_html_calculate_linkgenerate(request, first_name, download_uuid):
  # link, size = generate_link_311(ve)
  if request.LANGUAGE_CODE == 'en':
    url = 'https://www.device42.com/download_links/%s/' % download_uuid
  else:
    url = 'https://www.device42.com/%s/download_links/%s/' % (request.LANGUAGE_CODE, download_uuid)

  text1 = _("Hi %s,\n") % first_name
  text2 = _("""" \

Thank you for your interest in Device42. We have the virtual appliance link ready for you(link valid for a week). """)
  text3 = _("'Download link: ") + url
  text5 = _(""""

For getting started documentation and login info, please visit to: https://docs.device42.com/getstarted/

You can read about the latest release here: https://blog.device42.com/tag/release/

The appliance is production ready. Please let us know if you need an extended demo license.

After the install, you can refer to the quick start guide: https://docs.device42.com/device42-beginners-guide/

Please reply to this message with any comments or suggestions. We look forward to working with you!


Regards,
Device42 Support Team.
1-866-343-7242
""")

  html1 = _("<html><head></head><body>Hi %s,") % first_name
  html2 = _("""<p>Thank you for your interest in Device42. We have the virtual appliance link
    ready for you(valid for a week).
    """)
  html3 = _('</p><p>Download <a href="%(url)s">Here</a>.</p>') % {
    'url': url}
  html4 = ''
  html7 = _("""<p>
    The virtual appliance uses 2 vCPU, 8 GB RAM &amp; 100 GB of HDD. For installation and login info, please visit: <a  href="https://docs.device42.com/getstarted/">https://docs.device42.com/getstarted/</a>
    </p>

    <p>
    You can read about the latest release <a href="https://blog.device42.com/tag/release/">here.</a></p><p>The appliance is production ready. Please let us know if you need an extended demo license.</p>
    <p>Once the install is complete, you can refer to <a href="https://docs.device42.com/device42-beginners-guide/">the quick start guide.</a></p>
    <p>Please reply to this message with any comments or suggestions. We look forward to working with you!<p>
    Regards,<br>Device42 Support Team.<br>1-866-343-7242 <br>
     </body>
    </html>
    """)
  html_content = html1 + html2 + html3 + html4 + html7
  text_content = text1 + text2 + text3 + text5
  return text_content, html_content

def text_html_calculate_activategenerate(request, first_name, activation_uuid):
  # link, size = generate_link_311(ve)
  if request.LANGUAGE_CODE == 'en':
    url = 'https://www.device42.com/cloud_activation/%s/' % activation_uuid
  else:
    url = 'https://www.device42.com/%s/cloud_activation/%s/' % (request.LANGUAGE_CODE, activation_uuid)

  text1 = _("Hi %s,\n") % first_name
  text2 = _("Please open %s to confirm your email address. This activation link expires in 7 days.") % url
  text3 = _(""""

Regards,
Device42 Support Team.
1-866-343-7242
""")

  html1 = _("<html><head></head><body>Hi %s, <br>") % first_name
  html2 = _('<p>Please click <a href="%s">Here</a> to confirm your email address. This activation link expires in 7 days.</p><br>') % url
  html3 = _("""
    Regards,<br>Device42 Support Team.<br>1-866-343-7242
     </body>
    </html>
    """)

  html_content = html1 + html2 + html3
  text_content = text1 + text2 + text3
  return text_content, html_content

def text_html_calculate_datagenerate(request, cloud_instance, ots_url):

  text1 = _("Hi %s,\n\n") % cloud_instance.name
  text2 = _("""Thank you for your interest in Device42.

  Your cloud instance is ready for you at %s

  Username: %s
  Password: %s
  (Note: This is a one-time use link, once you view the password you will no longer be able to access it, please store in a secure location).

  To utilize the autodiscover functionality of Device42, you will require the Device42 Remote Collector that enables your cloud instance to remotely collect information that it would otherwise not have access to. You can download our Remote Collector and other discovery tools here: https://www.device42.com/autodiscovery/

  You can read about the latest release here: https://blog.device42.com/tag/release/

  Please read how to get started here: https://docs.device42.com/device42-beginners-guide/

  Please reply to this message with any comments or suggestions. We look forward to working with you!""") % (
    cloud_instance.cloud_url,
    cloud_instance.email,
    ots_url
  )
  text3 = _(""""

Regards,
Device42 Support Team.
1-866-343-7242
""")

  html1 = _("<html><head></head><body>Hi %s,<br><br>") % cloud_instance.name
  html2 = _("""Thank you for your interest in Device42. <br><br>

  Your cloud instance is ready for you at <a href="%s">%s</a><br><br>

  Username: %s<br>
  Password: %s<br>
  (Note: This is a one-time use link, once you view the password you will no longer be able to access it, please store in a secure location).<br><br>

  To utilize the autodiscover functionality of Device42, you will require the <a href="https://docs.device42.com/auto-discovery/remote-collector/">Device42 Remote Collector</a> that enables your cloud instance to remotely collect information that it would otherwise not have access to. You can download our Remote Collector and other discovery tools <a href="https://www.device42.com/autodiscovery/">here</a>.<br><br><br><br>

  You can read about the latest release <a href="https://blog.device42.com/tag/release/">here</a>.<br><br>

  Please read how to get started <a href="https://docs.device42.com/device42-beginners-guide/">here</a>.<br><br>

  Please reply to this message with any comments or suggestions. We look forward to working with you!<br><br>""") % (
    cloud_instance.cloud_url,
    cloud_instance.cloud_url,
    cloud_instance.email,
    ots_url
  )
  html3 = _("""
    Regards,<br>Device42 Support Team.<br>1-866-343-7242
     </body>
    </html>
    """)

  html_content = html1 + html2 + html3
  text_content = text1 + text2 + text3
  return text_content, html_content

def text_html_calculate_powerlink(platform, platform_title):
  link = generate_power_link(platform)
  text = _("""Hi,

Please click below to download the Device42 power appliance you recently requestsed.  This link is only valid for 72-hours from the time this email was sent.
  Platform: %s
  Download update: %s

For instruction on how to install and get started, go to: https://docs.device42.com/energy-monitoringmanagement/getting-started-with-power-and-environmental-monitoring/


Thank you,
Device42 Support Team
""") % (platform_title, link)
  html = _("""<html><head></head><body>Hi,
<p>Please <a href='%s'>click here</a> to download the Device42 power appliance for %s you recently requested.  This link is only valid for 72-hours from the time this email was sent.</p>
<p>For instructions on how to install and get started, <a href="https://docs.device42.com/energy-monitoringmanagement/getting-started-with-power-and-environmental-monitoring/">go here</a>.</p>
<br>
<em>Thank you</em>,<br>Device42 Support Team""") % (link, platform_title)
  return text, html
