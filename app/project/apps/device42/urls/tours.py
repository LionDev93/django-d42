from django.conf.urls import url
from project import views

tours_patterns = [
  url(r'^$', views.tours, name='tours'),
  url(r'^ssl-certificate-management/$', views.tours_ssl_certificate_management, name='tours_ssl_certificate_management'),
  url(r'^iso27001-compliance/$', views.tours_iso27001_compliance, name='tours_iso27001_compliance'),
  url(r'^server-room-management/$', views.tours_server_room_management, name='tours_server_room_management'),
  url(r'^manage-spare-parts/$', views.tours_manage_spare_parts, name='tours_manage_spare_parts'),
  url(r'^server-inventory/$', views.tours_server_inventory, name='tours_server_inventory'),
  url(r'^history-logs/$', views.tours_history_logs, name='tours_history_logs'),
  url(r'^data-center-documentation/$', views.tours_data_center_documentation, name='tours_data_center_documentation'),
  url(r'^server-rack-diagrams/$', views.tours_server_rack_diagrams, name='tours_server_rack_diagrams'),
  url(r'^cloud-migration/$', views.tours_cloud_migration,
      name="tours_cloud_migration"),
  url(r'^ip-address-management/$', views.abs301Redirect, {'token': 'tours_ip_address_tracking_software'}, name='tours_ipam'),
  url(r'^enterprise-password-management/$', views.abs301Redirect, {'token': 'features_password_management'}),
  url(r'^auto-discovery-tools/$', views.abs301Redirect, {'token': 'features_discovery'})
]
