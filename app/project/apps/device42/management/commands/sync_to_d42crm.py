from django.core.management.base import BaseCommand
import requests
import json

from project.apps.device42.models import (
    IDsProcessed, DownloadModel, UpdateModel, ContactModel,
    ScheduleModel, DownloadLinkTrack, CloudModel
)

CRMPUSERURL = 'https://registration.device42.com/api/1.0/addpotentialuser/'
#CRMPUSERURL = 'http://192.168.11.40:7000/api/1.0/addpotentialuser/'


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            processed_table = IDsProcessed.objects.get(id=1)
        except:
            processed_table = IDsProcessed.objects.create(
                id_processed_download=0,
                id_processed_contact=0,
                id_processed_demo=0,
                id_processed_update=0,
                id_processed_idc=0,
                id_processed_pricingcontact=0,
                id_processed_downloadlinktrack=0,
                id_processed_cloud=0)

        downloads = DownloadModel.objects.filter(
            id__gt=int(processed_table.id_processed_download))
        for download in downloads:
            # ipjson, rawoffval, digged  = resolve_ip(download[5].strip())
            user_data = {
                'name': download.name,
                'email': download.email,
                'time_linked': download.time_linked,
                'ip_addresses': download.ip_address,
                'clicky_cookie': download.clicky_cookie,
                'request_cookies': json.dumps(download.request_cookies),
                'first_action': 'download',
            }  # 'reverse_lookup':digged, 'dazzle': ipjson, 'tzone': rawoffval}
            r = requests.post(CRMPUSERURL, data=user_data, verify=False)
            # print r.content
            if r.status_code == 200:
                processed_table.id_processed_download = download.id
                processed_table.full_clean()
                processed_table.save()
            else: print 'error sending data'
        updates = UpdateModel.objects.filter(
            id__gt=processed_table.id_processed_update)
        for update in updates:
            # ipjson, rawoffval, digged  = resolve_ip(update[5].strip())
            user_data = {
                'email': update.email,
                'time_linked': update.time_linked,
                'ip_addresses': update.ip_address,
                'request_cookies': json.dumps(update.request_cookies),
                'first_action': 'update',
            }  # 'reverse_lookup':digged, 'dazzle': ipjson, 'tzone': rawoffval}
            r = requests.post(CRMPUSERURL, data=user_data, verify=False)
            # print r.content
            if r.status_code == 200:
                processed_table.id_processed_update = update.id
                processed_table.full_clean()
                processed_table.save()
            else:
              print 'error sending data'
        contacts = ContactModel.objects.filter(
            id__gt=processed_table.id_processed_contact)
        for contact in contacts:
            contact_info = ''
            if contact.phone:
                contact_info += contact.phone
            user_data = {
                'name': contact.name,
                'email': contact.email,
                'contact_info': contact_info,
                'time_linked': contact.time_linked,
                'ip_addresses': contact.ip_address,
                'clicky_cookie': contact.clicky_cookie,
                'request_cookies': json.dumps(contact.request_cookies),
                'first_action': 'contact',
            }
            r = requests.post(CRMPUSERURL, data=user_data, verify=False)
            # print r.content
            if r.status_code == 200:
                processed_table.id_processed_contact = contact.id
                processed_table.full_clean()
                processed_table.save()
            else:
              print 'error sending data'
        schedule_demos = ScheduleModel.objects.filter(
            id__gt=processed_table.id_processed_demo)
        for schedule_demo in schedule_demos:
            # ipjson, rawoffval, digged  = resolve_ip(schedule_demo[5].strip())
            user_data = {
                'name': schedule_demo.name,
                'email': schedule_demo.email,
                'time_linked': schedule_demo.time_linked,
                'ip_addresses': schedule_demo.ip_address,
                'clicky_cookie': schedule_demo.clicky_cookie,
                'request_cookies': json.dumps(schedule_demo.request_cookies),
                'first_action': 'schedule_demo',
            }  # 'reverse_lookup':digged, 'dazzle': ipjson, 'tzone': rawoffval}
            r = requests.post(CRMPUSERURL, data=user_data, verify=False)
            # print r.content
            if r.status_code == 200:
                processed_table.id_processed_demo = schedule_demo.id
                processed_table.full_clean()
                processed_table.save()
            else:
              print 'error sending data'
        downloadtracks = DownloadLinkTrack.objects.filter(
            id__gt=int(processed_table.id_processed_downloadlinktrack))
        for downloadtrack in downloadtracks:
            # ipjson, rawoffval, digged  = resolve_ip(downloadtrack[5].strip())
            user_data = {
                'name': downloadtrack.downloadmodel.name,
                'email': downloadtrack.downloadmodel.email,
                'request_cookies': downloadtrack.downloadmodel.request_cookies,
                'first_action': 'download_track',
            }
            # TODO: useful to track IP and cookie again in the above model and send it.
            r = requests.post(CRMPUSERURL, data=user_data, verify=False)
            # print r.content
            if r.status_code == 200:
                processed_table.id_processed_downloadlinktrack = downloadtrack.id
                processed_table.full_clean()
                processed_table.save()
            else:
              print 'error sending data'
        clouds = CloudModel.objects.filter(
          id__gt=int(processed_table.id_processed_cloud))
        for cloud in clouds:
            # ipjson, rawoffval, digged  = resolve_ip(cloud[5].strip())
            user_data = {
                'name': cloud.name,
                'email': cloud.email,
                'time_linked': cloud.time_linked,
                'ip_addresses': cloud.ip_address,
                'clicky_cookie': cloud.clicky_cookie,
                'request_cookies': json.dumps(cloud.request_cookies),
                'first_action': 'cloud',
            }  # 'reverse_lookup':digged, 'dazzle': ipjson, 'tzone': rawoffval}
            r = requests.post(CRMPUSERURL, data=user_data, verify=False)
            # print r.content
            if r.status_code == 200:
                processed_table.id_processed_cloud = cloud.id
                processed_table.full_clean()
                processed_table.save()
            else:
              print 'error sending data'
