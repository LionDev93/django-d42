import pytz
from django.conf import settings
from django.utils import timezone
from project.apps.upload.googleapi import GoogleDrive
from project.apps.upload.local_folder import LocalFolder


class UploadHandler(object):

    def __init__(self, request, notifier):
        self._file_obj = request.FILES.get('gdrive_file')
        self._email = request.POST.get('email')
        self._ticket_number = request.POST.get('ticket_number')
        self._request = request
        self._folder_path = self._get_folder_path()
        self._notifier = notifier
        self._backend = self._get_backend()

    def _get_backend(self):
        backends = {
            'google_drive': GoogleDrive,
            'local_folder': LocalFolder,
        }
        return backends[settings.UPLOADS_BACKEND](self)

    def do_upload(self):
        range_content = self._request.META.get('HTTP_X_CONTENT_RANGE')
        upload_id = self._request.META.get('HTTP_X_UPLOAD_ID')
        if range_content:
            file_name = self._request.META.get('HTTP_X_FILE_NAME')
            range_start, range_ends, file_size = self._parse_range_content(range_content, self._file_obj.size)
            return self._backend.upload_file_chunk(file_name, file_size, range_start, range_ends,
                                                   self._file_obj.read(), upload_id, self._folder_path)
        else:
            return self._backend.upload_file(self._file_obj.name, self._file_obj.size,
                                             self._file_obj.read(), self._folder_path)

    def _get_folder_path(self):
        folder_path = settings.UPLOADS_DESTINATION_FOLDER.split('/') + [self._email]
        if self._ticket_number:
            folder_path.append(self._ticket_number)
        else:
            timestamp = str(timezone.now().replace(tzinfo=pytz.UTC))
            folder_path += ['no_ticket_number', timestamp]
        return folder_path

    def _parse_range_content(self, range_content, chunk_size):
        if not range_content.startswith('bytes '):
            raise Exception('Unsuported range unit')
        try:
            range_content = range_content.replace('bytes ', '')
            range_parts = range_content.split('/')
            range_boundaries = range_parts[0]
            file_size = int(range_parts[1])
            boundaries = range_boundaries.split('-')
            range_start = int(boundaries[0])
            range_ends = int(boundaries[1])
            assert range_ends - range_start + 1 == chunk_size
            return range_start, range_ends, file_size
        except:
            raise Exception('Incorrect file range specification')

    def notify_upload_completed(self):
        self._notify('File uploaded')

    def send_notification(self, message):
        self._notify(message)

    def _notify(self, message):
        message_from = "Upload Page"
        origin = 'customer: %s' % self._email
        if self._ticket_number:
            origin += ', ticket: %s' % self._ticket_number
        message_body = '%s (%s)' % (message, origin)
        message_icon_emoji = ":satellite_antenna:"
        self._notifier.notify(message_body, message_from, message_icon_emoji)
