"""
website
(c) Device42 <dave.amato@device42.com>

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

import views, os, re
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.i18n import i18n_patterns
from django.core.urlresolvers import reverse
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import TemplateView, RedirectView
from django.http import HttpResponsePermanentRedirect
from django.views.i18n import javascript_catalog
from apps.device42.urls import company, customers, features, legal, partners, product, tours, vs, use_cases, videos, \
  case_studies, _misc

js_info_dict_app = {
  'packages': ('apps.device42',),
}

urlpatterns = [
  url(r'^sitemap\.xml$', TemplateView.as_view(template_name='sitemap.xml', content_type='text/xml')),
  url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
  url(r'^cloud_expired$', TemplateView.as_view(template_name='cloud_expired.html', content_type='text/html')),
  url(r'^open_source_license\.txt$',
      TemplateView.as_view(template_name='open_source_license.txt', content_type='text/plain')),
  url(r'^ajax/post/$', views.ajax_post, name='ajax-post'),
  url(r'^i18n/', include('django.conf.urls.i18n')),
  url(r'^jsi18n/$', views.javascript_catalog, js_info_dict_app, name='javascript-catalog'),
  url(r'^ajax_download/$', views.AjaxDownloadFill.as_view(), name='ajax-download'),
  url(r'^hubspot_form/$', views.HubSpotFormFill.as_view(), name='hubspot-form'),
]

# if settings.DEBUG:
#   urlpatterns += staticfiles_urlpatterns()

urlpatterns += i18n_patterns(
  url(r'^$', views.home, name="home"),
  url(r'^privacy/$', views.legal_privacy, name='legal_privacy'),
  url(r'^partners/', include(partners.partners_patterns)),
  url(r'^tours/', include(tours.tours_patterns)),
  url(r'^product/', include(product.product_patterns)),
  url(r'^customers/', include(customers.customers_patterns)),
  url(r'^features/', include(features.features_patterns)),
  url(r'^vs/', include(vs.vs_patterns)),
  url(r'^use-cases/', include(use_cases.use_case_patterns)),
  url(r'^videos/', include(videos.videos_patterns)),
  url(r'^webinar-videos/', views.webinar_videos, name='webinar_videos'),
  url(r'^case-studies/', include(case_studies.case_studies_patterns)),
  #
  url(r'^download/$', views.download, name="download"),
  url(r'^it-as-a-service/$', views.itaas_form, name="itaas_form"),
  url(r'^whitepapers/idc-it-agility-business-alignment/$', views.idc_form, name="idc_form"),
  url(r'^download-submit/$', views.download_links, name="download_links"),
  url(r'^integrations/$', views.integrations, name='integrations'),
  url(r'^integrations/(?P<slug>[a-zA-Z0-9_.-]+)/$', views.integrations_detail,
     name='integrations_detail'),
  url(r'^software/$', views.software, name='software'),
  url(r'^software/(?P<token>[a-zA-Z0-9_.-]+)/$', views.abs301Redirect,
      name='software_detail'),
  url(r'^migrations/$', views.migrations, name='migrations'),
  url(r'^migrations/(?P<product>[a-zA-Z0-9_.-]+)/$', views.migrations_detail,
      name='migrations_detail'),
  url(r'^download_links/id/(?P<id>.*)/$', views.download_links, name='download-link-id'),
  url(r'^download_links/(?P<download_uuid>[a-z0-9-]+)/$', views.download_links, name='download-link'),
  url(r'^cloud_activation/(?P<activation_uuid>[a-z0-9-]+)/$', views.cloud_activation, name='cloud_activation'),
  url(r'^thanks/(?P<id>\d+)/$', views.thanks, name='thanks'),
  url(r'^schedule_demo/$', views.schedule_form, name="schedule_form"),
  url(r'^offers/(?P<partner>\w+(-\w+)*)/$', views.offers, name='offers'),
  url(r'^it-coloring-book/$', views.it_coloring_book, name='it-coloring-book'),
  url(r'^vulndb/$', views.vulndb, name='vulndb'),
  url(r'^support/$', views.support, name='support'),
  url(r'^update/$', views.software_detail, {'package': 'update'}, name='update'),
  url(r'^pricing-power/$', views.faq_power, name='faq_power'),
  url(r'^faq/$', views.faq_sales, name='faq_sales'),
  url(r'^vulnerability-management-software/$', RedirectView.as_view(url='/')),
  url(r'^new_ticket/$',
      RedirectView.as_view(url='https://support.device42.com/hc/en-us/requests/new'),
      name='new_ticket'),
  url(r'^open-source/$', views.opensource, name='opensource'),
  url(r'^opensource/$', views.abs301Redirect, {'token':'opensource'}),
  url(r'^feedback/$', views.thanks, {'id': '4'}, name='feedback'),
  url(r'^udpate/$', views.abs301Redirect, {'token': 'update'}),
  url(r'^beta/$', RedirectView.as_view(url='/download/')),
  url(r'^power-appliance/$',  views.abs301Redirect, {'token':'autodiscovery'}),
  url(r'^power_appliance/$', views.abs301Redirect, {'token':'autodiscovery'}),
  url(r'^upload/$', views.upload, name='upload'),
  #----------------------
  # rooted urls
  #
  # partners
  url(r'^find_partner/$', views.partners_find, name='partners_find'),
  url(r'^apply_partner/$', views.partners_learnmore, name='partners_learnmore'),
  url(r'^register_deal/$', views.partners_register, name='partners_register'),
  url(r'^partner-benefits/$', views.partners_benefits, name='partners_benefits'),
  # tours
  url(r'^patch-panel-cable-management-software/$', views.tours_patch_cable_management,
      name='tours_patch_cable_management'),
  url(r'^it-inventory-management-software/$', views.abs301Redirect, {'token': 'features_itam'},
      name='tours_it_inventory_management'),
  url(r'^data-center-power-management/$', views.tours_data_center_power_management,
      name='tours_data_center_power_management'),
  url(r'^ip-address-tracking-software/$', views.abs301Redirect, {'token': 'features_ipam'},
      name='tours_ip_address_tracking_software'),
  # legal
  url(r'^d42_open_disc_eula/$', views.legal_d42_open_disc_eula, name='legal_d42_open_disc_eula'),
  url(r'^eula/$', views.legal_eula, name='legal_eula'),
  url(r'^privacy/$', views.legal_privacy, name='legal_privacy'),
  url(r'^social/$', views.customers_social_mentions, name="customers_social_mentions"),
  # url(r'^testimonials/$', views.customers_testimonials, name='customers_testimonials'),
  url(r'^testimonials/$', views.abs301Redirect, {'token': 'customers'}),
  # compare
  url(r'^compare/$', views.compare, name='compare'),
  url(r'^compare-dcim/$', views.compare_dcim, name='compare_dcim'),
  url(r'^compare-cmdb/$', views.compare_cmdb, name='compare_cmdb'),
  url(r'^compare-ipam/$', views.compare_ipam, name='compare_ipam'),
  url(r'^roi_calculator/$', views.roi_calculator, name='roi_calculator'),
  # product
  url(r'^pricing/$', views.product_pricing, name='product_pricing'),
  url(r'^benefits/$', views.product_benefits, name='product_benefits'),
  # company
  url(r'^$', views.company, name='company'),
  url(r'^about/$', views.company_about, name='company_about'),
  url(r'^contact/$', views.company_contact, name='company_contact'),
  url(r'^about/$', views.company_about, name='company_about'),
  url(r'^jobs/$', views.company_jobs, name='company_jobs'),
  url(r'^jobs/devops-evangelist/$', views.company_jobs_devops, name='company_jobs_devops'),
  # software
  url(r'^opendiscovery/$', views.abs301Redirect, {'token': 'features_discovery'}),
  url(r'^autodiscovery/$', views.software_detail, {'package': 'autodiscovery'},
      name='autodiscovery'),
  url(r'^bulk-data-management/$', views.software_detail, {'package': 'bulk-data-management'},
      name='bulk-data-management'),
  url(r'^miscellaneous-tools/$', views.software_detail, {'package': 'miscellaneous-tools'},
      name='miscellaneous-tools'),
  # redirect + client promos
  url(r'^cyberlogic-solutions/$', views.cyberlogic_solutions, name='cyberlogic_solutions'),
  url(r'^koozie/$', views.koozie, name='koozie'),
  url(r'^koozie.*/$', RedirectView.as_view(url='/koozie')),
  url(r'^KOOZIE/$', RedirectView.as_view(url='/koozie')),
  # url(r'^LISA16/$', views.lisa16, name='lisa16'),
  url(r'^LISA16/$', RedirectView.as_view(url='/koozie')),
  url(r'^LISA16.*/$', RedirectView.as_view(url='/koozie')),
  url(r'^lisa16/$', RedirectView.as_view(url='/koozie')),
  url(r'^LISA17/$', RedirectView.as_view(url='/koozie')),
  url(r'^LISA17.*/$', RedirectView.as_view(url='/koozie')),
  url(r'^lisa17/$', RedirectView.as_view(url='/koozie')),

  url(r'^lisa17-survey-results/$', views.lisa_survey_results, name='lisa_survey_results'),

  url(r'^it-adult-coloring-book/$', RedirectView.as_view(url='/it-coloring-book/')),
  url(r'^newsletter/$', RedirectView.as_view(url='/')), #TODO: its own page
  url(r'^new_feature/$', RedirectView.as_view(url='https://support.device42.com/hc/en-us/community/topics/200836648-Feature-Requests')),
  url(r'^new_ticket/', RedirectView.as_view(url='https://support.device42.com/hc/en-us/requests/new')),
  url(r'^new_feedback/', RedirectView.as_view(url='/thanks/4')),
  url(r'^inviteme/', RedirectView.as_view(url= '/download/')),
  url(r'^pingsweep_twitter/', RedirectView.as_view(url= 'https://twitter.com/device42/')),
  url(r'^twitter_od/', RedirectView.as_view(url= 'https://twitter.com/device42/')),
  url(r'^it-adult-coloring-book/$', RedirectView.as_view(url='/it-coloring-book/')),
  url(r'^sysadmin-day-giveaway/$', RedirectView.as_view(url='/it-coloring-book/')),
  # for webniar registeration
  url(r'^register-for-webinar/$', views.register_for_webinar, name='register_for_webinar'),
  url(r'^register-for-webinar-complete/$', views.register_for_webinar_complete, name='register_for_webinar_complete'),
  # for webinar2 registration
  url(r'^register-for-webinar2/$', views.register_for_webinar2, name='register_for_webinar2'),
  url(r'^register-for-webinar2-complete/$', views.register_for_webinar2_complete, name='register_for_webinar2_complete'),
  # for webinar3 registration
  url(r'^register-for-webinar3/$', views.register_for_webinar3, name='register_for_webinar3'),
  url(r'^register-for-webinar3-complete/$', views.register_for_webinar3_complete, name='register_for_webinar3_complete'),
  url(r'^webinars/automating-servicenow-registration/$', views.automating_servicenow_registeration, name='automating_servicenow_registeration'),
  url(r'^webinars/thank-you-for-registering/$', views.thank_you_for_registering, name='thank_you_for_registering'),

  url(r'^solutions/bmc-remedy/$', views.solutions_bmc_remedy, name='solutions_bmc_remedy'),
  url(r'^solutions/jira/$', views.solutions_jira, name='solutions_jira'),
  url(r'^solutions/zendesk/$', views.solutions_zendesk, name='solutions_zendesk'),
  url(r'^solutions/samanage/$', views.solutions_samanage, name='solutions_samanage'),
  url(r'^solutions/hpsm/$', views.solutions_hpsm, name='solutions_hpsm'),
  url(r'^solutions/service-now/$', views.solutions_service_now, name='solutions_service_now'),
  url(r'^solutions/servicenow-express/$', views.solutions_servicenow_express, name='solutions_servicenow_express'),

  url(r'^solutions/dl-idc-emc-wp/$', views.dl_idc_emc_wp, name='dl-idc-emc-wp'),
  url(r'^solutions/(?P<slug>[a-zA-Z0-9_.-]+)/$', views.solutions_generator, name='solutions_generator'),

  url(r'^free-tools/dc-doc-template/$', views.free_tools_doc_template, name='free_tools_doc_template'),
  url(r'^free-tools/dc-doc-template-dl/$', views.free_tools_doc_template_dl, name='free_tools_doc_template_dl'),
  url(r'^cookies/$', views.cookies, name='cookies'),
  prefix_default_language=False
)

#urlpatterns = urls

#ADDS ADWORD PAGES RECURSIVELY
for fileName in os.listdir(os.path.join(settings.TEMPLATE_CONTENT_URLS, 'landing')):
  if fileName.endswith('.html') and (fileName.startswith('Device42-')):
    m = re.search(r'Device42-(.*).html', fileName)
    slug = m.group(1)
    urlpatterns += i18n_patterns(url(r'^solution/' + slug.lower() + '/$',
                                     TemplateView.as_view(template_name=('landing/%s' % fileName)),
                                     name=('solutions_%s' % slug.lower().replace('-', '_'))),
                                 prefix_default_language=False)

"""
Case insensitive:
url(r'^(?i)landing/' + slug.lower() + '/$'....
"""

# from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# urlpatterns += staticfiles_urlpatterns()
