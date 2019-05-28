import requests
from django.conf import settings
from oauth2client import service_account
from urlparse import urlparse, parse_qs


class GoogleDrive(object):

    def __init__(self, controller):
        self._token = self.authenticate()
        self._controller = controller

    def authenticate(self):
        scopes = ['https://www.googleapis.com/auth/drive']
        credentials = service_account.ServiceAccountCredentials.from_json_keyfile_name(
            settings.GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE, scopes=scopes)
        delegated_credentials = credentials.create_delegated(settings.GOOGLE_DRIVE_DELEGATED_ACCOUNT)
        return delegated_credentials.get_access_token().access_token

    def upload_file(self, filename, file_size, file_data, folder_path):
        upload_url = self._get_upload_url(filename, file_size, None, folder_path)
        resp = self._upload_full_file_data(upload_url, file_size, file_data)
        return self._is_upload_completed(resp)

    def upload_file_chunk(self, filename, file_size, range_start, range_ends, file_chunk_data, upload_id, folder_path):
        upload_url = self._get_upload_url(filename, file_size, upload_id, folder_path)
        if not upload_id:
            upload_id = self._extract_upload_id(upload_url)
        resp = self._upload_file_chunk_data(upload_url, file_size, range_start, range_ends, file_chunk_data)
        return self._is_upload_completed(resp) or upload_id

    def _get_upload_url(self, filename, file_size, upload_id, folder_path):
        return ('https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&upload_id=%s' % upload_id
                if upload_id else self._start_file_upload(filename, file_size, folder_path))

    def _extract_upload_id(self, upload_url):
        try:
            url_parts = urlparse(upload_url)
            query_params = parse_qs(url_parts.query)
            return query_params['upload_id'][0]
        except:
            raise Exception('Unexpected upload URL format')

    def _get_base_headers(self):
        return {'Authorization': 'Bearer %s' % self._token}

    def _start_file_upload(self, filename, file_size, folder_path):
        url = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable'
        folder_id = self._get_folder_id(folder_path)
        headers = self._get_base_headers()
        headers.update({'X-Upload-Content-Length': str(file_size)})
        file_metadata = {
            'name': filename,
            'parents': [folder_id],
        }
        resp = requests.post(url, headers=headers, json=file_metadata)
        if resp.status_code != 200:
            raise Exception('Bad upload initialization')
        return resp.headers['Location']

    def _get_folder_id(self, folder_path):
        root_folder_name = folder_path.pop(0)
        folder_id = self._get_child_folder_id(root_folder_name, is_root_folder=True)
        while folder_path:
            next_folder_name = folder_path.pop(0)
            folder_id = self._get_child_folder_id(next_folder_name, parent_id=folder_id)
        return folder_id

    def _get_child_folder_id(self, folder_name, parent_id=None, is_root_folder=False):
        url = ("https://www.googleapis.com/drive/v3/files?q=name = '%s' and "
               "mimeType = 'application/vnd.google-apps.folder'" % folder_name)
        if parent_id:
            url += " and '%s' in parents" % parent_id
        if is_root_folder:
            url += " and '%s' in owners" % settings.UPLOADS_FOLDER_OWNER
        headers = self._get_base_headers()
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise Exception('Could not create organization structure in backend cloud')
        folders = resp.json()['files']
        folders = filter(lambda item: not item.get('parents'), folders) if not parent_id else folders
        if folders:
            return folders[0]['id']
        elif is_root_folder:
            raise Exception('Destination folder not found')
        else:
            return self._create_folder(folder_name, parent_id)

    def _create_folder(self, folder_name, parent_id=None):
        url = 'https://www.googleapis.com/drive/v3/files'
        headers = self._get_base_headers()
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id] if parent_id else []
        }
        resp = requests.post(url, headers=headers, json=folder_metadata)
        if resp.status_code != 200:
            raise Exception('Could not create organization structure in backend cloud')
        folder_id = resp.json()['id']
        return folder_id

    def _upload_full_file_data(self, upload_url, file_size, file_data):
        headers = self._get_base_headers()
        headers.update({'Content-Length': str(file_size)})
        return requests.put(upload_url, headers=headers, data=file_data)

    def _upload_file_chunk_data(self, upload_url, file_size, range_start, range_ends, file_chunk_data):
        chunk_size = range_ends - range_start + 1
        headers = self._get_base_headers()
        headers.update({'Content-Length': str(chunk_size)})
        headers.update({'Content-Range': 'bytes %i-%i/%i' % (range_start, range_ends, file_size)})
        return requests.put(upload_url, headers=headers, data=file_chunk_data)

    def _is_upload_completed(self, response):
        if response.status_code in [200, 201]:
            return self._upload_completed()
        elif response.status_code == 308:
            return False
        else:
            notification = 'An upload attempt to Google Drive has returned an error. Google Drive response details: %i: %s' % (response.status_code, response.json()['error']['message'])
            self._controller.send_notification(notification)
            raise Exception('Error while uploading to backend cloud: %i' % response.status_code)

    def _upload_completed(self):
        self._controller.notify_upload_completed()
        return True

    def _grant_access(self, gdrive_file_id):
        """
        Unused / Deprecated
        """
        url = 'https://www.googleapis.com/drive/v3/files/%s/permissions?sendNotificationEmail=false' % gdrive_file_id
        headers = self._get_base_headers()
        permission_data = {
            'type': 'user',
            'role': 'reader'
        }
        users_to_gran_access = settings.GOOGLE_DRIVE_GRANT_ACCESS
        for email_address in users_to_gran_access:
            self._create_user_permission(url, headers, email_address, permission_data)

    def _create_user_permission(self, url, headers, email_address, permission_data):
        user_permission = permission_data.copy()
        user_permission.update({'emailAddress': email_address})
        resp = requests.post(url, headers=headers, json=user_permission)
        if resp.status_code not in [200, 201]:
            raise Exception('Could not grant access to user identified as: %s' % email_address)
