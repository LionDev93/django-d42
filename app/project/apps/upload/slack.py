import logging
import requests
from django.conf import settings


class SlackNotifier(object):

    def notify(self, message_body, message_from, message_icon_emoji):
        logging.info('Sending Slack notification')
        url = settings.UPLOADS_SLACK_NOTIFICATION_HOOK
        message_data = {
            "text": message_body,
            "username": message_from,
            "icon_emoji": message_icon_emoji
        }
        resp = requests.post(url, json=message_data)
        if resp.status_code != 200:
            logging.error('Could not send Slack notification: %s' % resp.content)
