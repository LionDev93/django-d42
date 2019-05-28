from django.conf import settings
from django.core.cache import cache
from os import makedirs, chown, chmod, getgid, stat, access, R_OK, W_OK
from os.path import join, exists
from pwd import getpwnam
from uuid import uuid4


class LocalFolder(object):

    def __init__(self, controller):
        self._controller = controller

    def upload_file(self, filename, file_size, file_data, folder_path):
        try:
            file_obj, _ = self._get_file(filename, folder_path)
            file_obj.write(file_data)
            file_obj.close()
            return self._is_upload_completed(file_obj)
        except Exception as ex:
            return self._is_upload_completed(ex)

    def upload_file_chunk(self, filename, file_size, range_start, range_ends, file_chunk_data, upload_id, folder_path):
        try:
            file_obj, upload_id = self._get_file(filename, folder_path, upload_id)
            file_obj = self._write_file_chunk_data(file_obj, file_size, range_start, range_ends, file_chunk_data, upload_id)
            return self._is_upload_completed(file_obj) or upload_id
        except Exception as ex:
            return self._is_upload_completed(ex)

    def _get_file(self, filename, folder_path, upload_id=None):
        if upload_id:
            file_path = cache.get(upload_id)
        else:
            folder_path = self._ensure_folder_access(folder_path)
            file_path = join(folder_path, filename)
            upload_id = str(uuid4())
            cache.set(upload_id, file_path)
        file_obj = open(file_path, 'ab')
        return file_obj, upload_id

    def _ensure_folder_access(self, folder_path):
        prefix = '/' if folder_path[0] == '' else ''
        container_folder_path = prefix + join(*folder_path[:-3])
        folder_path = prefix + join(*folder_path)
        uid = getpwnam(settings.UPLOADS_FOLDER_OWNER)[2]
        for path in container_folder_path, folder_path:
            if exists(path):
                status = stat(path)
                if status.st_uid != uid:
                    raise Exception('Destination folder %s is not owned by user: %s' % (path, settings.UPLOADS_FOLDER_OWNER))
                if not access(path, R_OK|W_OK):
                    raise Exception('Destination folder %s is not accessible by the current process' % path)
            else:
                makedirs(path)
                chown(path, uid, getgid())
                chmod(path, 0770)
        return folder_path

    def _write_file_chunk_data(self, file_obj, file_size, range_start, range_ends, file_chunk_data, upload_id):
        chunk_size = range_ends - range_start + 1
        file_obj.seek(range_start)
        file_obj.write(file_chunk_data[:chunk_size])
        if range_ends == file_size - 1:
            file_obj.close()
            cache.delete(upload_id)
        return file_obj

    def _is_upload_completed(self, result):
        if isinstance(result, file) and result.closed:
            return self._upload_completed()
        elif isinstance(result, file) and not result.closed:
            result.close()
            return False
        else:
            notification = 'An upload attempt to local storage on Device42 server failed. Error was: %s' % str(result)
            self._controller.send_notification(notification)
            raise Exception('Error while uploading to backend cloud')

    def _upload_completed(self):
        self._controller.notify_upload_completed()
        return True
