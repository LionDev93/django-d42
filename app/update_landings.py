import markdown
import os
import shutil
import json
from PIL import Image, ImageOps

dir_path = os.path.dirname(os.path.realpath(__file__))

landing_slugs = os.listdir(os.path.join(dir_path, "landings"))

landings_data = {}

for landing_slug in landing_slugs:
  if landing_slug == "_specs": continue

  file_name = os.path.join(dir_path, "landings", landing_slug, 'content.txt')
  with open(file_name, 'r') as content_file:
    content = content_file.read()
    landing_data = {}
    current_element_name = ""
    current_element_index = -1
    current_field_name = ""
    for line in content.split("\n"):
      line = line.strip()
      if line.startswith("#template="):
        landing_data['template'] = line.replace('#template=', '').strip()
      elif line.startswith("[") and line.endswith("]"): # start of the new block
        new_element_name, new_field_name = line.strip("[]").split('.')

        if new_element_name.endswith("]"):
          new_element_name, new_element_index = new_element_name.split("[")
          new_element_index = int(new_element_index.rstrip("]")) - 1
        else:
          new_element_index = -1

        if current_field_name != new_field_name or current_element_name != new_element_name or current_element_index != current_element_index:
          if current_element_name in landing_data:
            if current_element_index == -1:
              if current_field_name == 'content':
                try:
                  landing_data[current_element_name][current_field_name] = markdown.markdown(landing_data[current_element_name][current_field_name].encode('utf-8').strip().decode('utf-8'))
                except:
                  landing_data[current_element_name][current_field_name] = markdown.markdown(landing_data[current_element_name][current_field_name].encode('cp1252').strip().decode('utf-8'))
              else:
                landing_data[current_element_name][current_field_name] = landing_data[current_element_name][current_field_name].strip()
            else:
              if current_field_name == 'content':
                try:
                  landing_data[current_element_name][current_element_index][current_field_name] = markdown.markdown(landing_data[current_element_name][current_element_index][current_field_name].encode('utf-8').strip().decode('utf-8'))
                except:
                  landing_data[current_element_name][current_element_index][current_field_name] = markdown.markdown(landing_data[current_element_name][current_element_index][current_field_name].encode('cp1252').strip().decode('utf-8'))
              else:
                landing_data[current_element_name][current_element_index][current_field_name] = landing_data[current_element_name][current_element_index][current_field_name].strip()

        current_field_name = new_field_name
        current_element_name = new_element_name
        current_element_index = new_element_index

        if current_element_name not in landing_data:
          if current_element_index >= 0:
            landing_data[current_element_name] = []
          else:
            landing_data[current_element_name] = {}
      else:
        if current_element_name.strip() == '' or current_field_name.strip() == '': continue
        if current_element_index == -1:
          if current_field_name not in landing_data[current_element_name]:
            try:
              landing_data[current_element_name][current_field_name] = line.decode('utf-8') + "\n"
            except:
              landing_data[current_element_name][current_field_name] = line.decode('cp1252') + "\n"

          else:
            try:
              landing_data[current_element_name][current_field_name] += line.decode('utf-8') + "\n"
            except:
              landing_data[current_element_name][current_field_name] += line.decode('cp1252') + "\n"
        else:
          if len(landing_data[current_element_name]) < current_element_index+1: landing_data[current_element_name].append({})

          if current_field_name not in landing_data[current_element_name][current_element_index]:
            try:
              landing_data[current_element_name][current_element_index][current_field_name] = line.decode('utf-8') + "\n"
            except:
              landing_data[current_element_name][current_element_index][current_field_name] = line.decode('cp1252') + "\n"
          else:
            try:
              landing_data[current_element_name][current_element_index][current_field_name] += line.decode('utf-8') + "\n"
            except:
              landing_data[current_element_name][current_element_index][current_field_name] += line.decode('cp1252') + "\n"

    if current_element_name in landing_data:
      if current_element_index == -1:
        if current_field_name == 'content':
          try:
            landing_data[current_element_name][current_field_name] = markdown.markdown(landing_data[current_element_name][current_field_name].encode('utf-8').strip().decode('utf-8'))
          except:
            landing_data[current_element_name][current_field_name] = markdown.markdown(landing_data[current_element_name][current_field_name].encode('cp1252').strip().decode('utf-8'))
        else:
          try:
            landing_data[current_element_name][current_field_name] = landing_data[current_element_name][current_field_name].strip().decode('utf-8')
          except:
            landing_data[current_element_name][current_field_name] = landing_data[current_element_name][current_field_name].strip().decode('cp1252')
      else:
        if current_field_name == 'content':
          try:
            landing_data[current_element_name][current_element_index][current_field_name] = markdown.markdown(landing_data[current_element_name][current_element_index][current_field_name].encode('utf-8').strip().decode('utf-8'))
          except:
            landing_data[current_element_name][current_element_index][current_field_name] = markdown.markdown(landing_data[current_element_name][current_element_index][current_field_name].encode('cp1252').strip().decode('utf-8'))
        else:
          try:
            landing_data[current_element_name][current_element_index][current_field_name] = landing_data[current_element_name][current_element_index][current_field_name].strip().decode('utf-8')
          except:
            landing_data[current_element_name][current_element_index][current_field_name] = landing_data[current_element_name][current_element_index][current_field_name].strip().decode('cp1252')

    landing_data['slug'] = landing_slug
    landing_data['images'] = {}
    landings_data[landing_slug] = landing_data
  # /Content Processing

  spec_name = 'layout-1.txt'
  if 'template' in landings_data[landing_slug]:
    spec_name = landings_data[landing_slug]['template'].split('/')[1].replace('.html', '.txt').strip()

  with open(os.path.join(dir_path, "landings", "_specs", spec_name), 'r') as spec_file:
    img_spec = json.loads(spec_file.read())

    landing_files = os.listdir(os.path.join(dir_path, "landings", landing_slug))
    for landing_file_name in landing_files:
        file_name, file_extension = landing_file_name.split('.')

        if file_extension not in ['jpeg', 'jpg', 'png', 'gif']: continue

        if '-' not in file_name:
          landings_data[landing_slug]['images'][file_name] = file_extension
          landings_data[landing_slug][file_name]['image_url'] = 'img/landings/%s-%s.%s' % (landing_slug, file_name, file_extension)
        else:
          file_name, file_number = file_name.split('-')
          if file_name not in landings_data[landing_slug]['images']:
            landings_data[landing_slug]['images'][file_name] = {}

          if int(file_number)-1 < len(landings_data[landing_slug][file_name]):
            landings_data[landing_slug][file_name][int(file_number)-1]['image_url'] = 'img/landings/%s-%s-%d.%s' % (landing_slug, file_name, int(file_number), file_extension)
          else:
            print 'LS', landing_slug, 'FN', file_name, 'NB', file_number, len(landings_data[landing_slug][file_name])

        original_image = os.path.join(dir_path, "landings", landing_slug, landing_file_name)
        new_image = os.path.join(dir_path, "static", "img", "landings", "%s-%s" % (landing_slug, landing_file_name))

        if file_extension not in ['gif']:
          img = Image.open(original_image)
          img = ImageOps.fit(img, img_spec[file_name], Image.LANCZOS)
          img.save(new_image)
        else:
          shutil.copy(original_image, new_image)


  file_content = "import json\n\n"
  ld = json.dumps(landings_data)
  ld = ld.replace('\n', '').replace('\\', '\\\\').replace("\'", "\\'").replace('\"', '\\"')
  file_content += "LANDING_DATA = json.loads('%s')" % ld

  with open(os.path.join(dir_path, "project", "apps", "device42", "landings.py"), 'w') as lf:
    lf.write(file_content)



