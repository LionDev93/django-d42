from django.conf.urls import url
from django.views.generic.base import RedirectView
from project import views


features_patterns = [
  url(r'^$', views.features, name="features"),
  url(r'^data-center-management/$', views.features_dcim, name='features_dcim'),
  url(r'^it-asset-management/$', views.features_itam, name='features_itam'),
  url(r'^ip-address-management/$', views.features_ipam, name='features_ipam'),
  url(r'^device-discovery/$', views.features_discovery, name='features_discovery'),
  url(r'^role-based-access/$', views.features_role_based_access, name='features_role_based_access'),
  url(r'^application-mappings/$', views.features_app_mapping, name='features_app_mapping'),
  url(r'^software-license-management/$', views.features_software_license, name='features_software_license'),
  url(r'^enterprise-password-management/$', views.features_password_management, name='features_password_management'),
  url(r'^cmdb/$', views.features_cmdb_for_cloud_era, name='features_cmdb_for_cloud_era'),
  url(r'^integrations/$', views.features_integrations, name='features_integrations'),
  url(r'^cloud-recommendation-engine/$', views.features_cloud_recommendation, name='features_cloud_recommendation'),
  url(r'^affinity-groups/$', views.features_affinity_groups, name='features_affinity_groups'),
  #
  #  redirects
  url(r'^password_management/$', views.abs301Redirect, {'token':'features_password_management'}),
  url(r'^data_center_management/$', views.abs301Redirect, {'token': 'features_dcim'}),
  url(r'^auto-discovery/$', views.abs301Redirect, {'token': 'features_discovery'}),
  url(r'^ip_address_management/$', views.abs301Redirect, {'token':'features_ipam'}),
  url(r'^password-management/$', views.abs301Redirect, {'token': 'features_password_management'}),
]
