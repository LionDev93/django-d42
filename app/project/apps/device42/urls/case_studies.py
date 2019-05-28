from django.conf.urls import url
from project import views

case_studies_patterns = [
  url(r'^$', views.customers_case_studies, name='customers_case_studies'),
  url(r'^Coventry-University/$', views.case_studies_coventry_university, name='case_studies_coventry_university'),
  url(r'^Maxihost/$', views.case_studies_maxihost, name='case_studies_maxihost'),
  url(r'^Intl-Financial-Service-Provider/$', views.case_studies_intl_financial_service_provider,
      name='case_studies_intl_financial_service_provider'),
  url(r'^AppDirect/$', views.case_studies_appdirect, name='case_studies_appdirect'),
  url(r'^Gravity-RD/$', views.case_studies_gravity_rd, name='case_studies_gravity'),
  url(r'^Netcetera/$', views.case_studies_netcetera_group, name='case_studies_netcetera'),
  url(r'^Dell-EMC/$', views.case_studies_dell_emc, name='case_studies_dell_emc'),
  url(r'^largest-virtualization-company/$', views.largest_virt_company, name='largest_virt_company'),
]
