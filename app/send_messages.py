from poeditor import POEditorAPI
import subprocess
import os

current_path = os.path.dirname(os.path.realpath(__file__))
PROJECT_ID = '93047'
API_KEY = 'c6b59628097c864bd70397a828e542da'


subprocess.check_output(['python', 'manage.py', 'makemessages', '-l', 'en',
                         '--ignore=*jobs*', '--ignore=*templates/landing/*', '--ignore=*templates/sections/legal/*',
                         '--ignore=*opendiscovery*'], cwd=current_path)

client = POEditorAPI(api_token=API_KEY)
client.update_terms('93047', file_path=current_path + '/locale/en/LC_MESSAGES/django.po')
