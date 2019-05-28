from django.conf import settings
import not_translated

valid_language_codes = [lang[0] for lang in settings.LANGUAGES]


def get_d42_language(request):
  """retrieves the context requests langauage_code (Defaults to en)"""
  if not request.LANGUAGE_CODE or not request.LANGUAGE_CODE in valid_language_codes:
    return "en"
  else:
    return request.LANGUAGE_CODE


def set_d42_language(request):
  """sets the language code to prepend URL with"""
  lang = get_d42_language(request)
  return {'D42_LANGUAGE': lang}


def get_d42_locale_url(request):
  """retrieves i18n formatted URL"""
  lang = get_d42_language(request)
  if lang == 'en':
    return ""
  else:
    return "/" + lang


def set_d42_locale_url(request):
  """sets language code to prepend URL with"""
  url_prep = get_d42_locale_url(request)
  return {'URL_PREPEND': url_prep}


def site_url(request):
  """retrieves the static domain from settings"""
  url_domain = settings.STATIC_DOMAIN
  return {'STATIC_DOMAIN': url_domain}


def check_translated(request):
  """checks if page (by URL) is translated"""
  translated = True
  try:
    for nt in not_translated:
      if nt in request.path:
        translated = False
  except:
    pass

  return {'D42_TRANSLATED': translated}


def recaptcha(request):
  """returns public-facing recaptcha key"""
  return {
    'GOOGLE_RECAPTCHA_SITE_KEY': settings.GOOGLE_RECAPTCHA_SITE_KEY,
  }
