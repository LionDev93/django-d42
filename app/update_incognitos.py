import os
import json
import requests


json_data = requests.get('https://raw.githubusercontent.com/ivolo/disposable-email-domains/master/index.json').json()
dir_path = os.path.dirname(os.path.realpath(__file__))

# validate before update
if len(json_data) > 0 and type(json_data) == list:
  incognitos_file = open(dir_path + '/project/apps/device42/incognitos.json', 'w')
  incognitos_file.write(str(json.dumps(json_data)))
  incognitos_file.close()

with open(dir_path + '/project/apps/device42/incognitos_manual.json') as data_file:
  manual = json.load(data_file)

try:
  with open(dir_path + '/project/apps/device42/incognitos.json') as data_file:
    INCOGNITO_LIST = json.load(data_file) + manual
except:
  INCOGNITO_LIST = manual

incognitos_file = open(dir_path + '/project/apps/device42/incognitos.py', 'w')
incognitos_file.write('INCOGNITO_LIST = '+str(INCOGNITO_LIST))
incognitos_file.close()
