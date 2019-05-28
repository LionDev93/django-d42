from django.conf.urls import url
from project import views

vs_patterns = [
  url(r'^$', views.vs_index_page, name='compare'),
  url(r'^nlyte/$', views.compare_nlyte, name='compare_nlyte'),
  url(r'^servicenow/$', views.compare_servicenow, name='compare_servicenow'),
  url(r'^servicewatch/$', views.compare_servicewatch, name='compare_servicewatch'),
  url(r'^bmc-atrium/$', views.compare_bmc_atrium, name='compare_bmc_atrium'),
  url(r'^hp-ucmdb/$', views.compare_hp_ucmdb, name='compare_hp_ucmdb'),
  url(r'^solarwinds/$', views.compare_solarwinds, name='compare_solarwinds'),
  url(r'^sunbird/$', views.compare_sunbird, name='compare_sunbird'),
  url(r'^infoblox/$', views.compare_infoblox, name='compare_infoblox'),
  url(r'^risc-networks/$', views.compare_risc, name='compare_risc'),
  url(r'^bmc-discovery/$', views.compare_bmc_discovery, name='compare_bmc_discovery'),
  url(r'^racktables/$', views.compare_racktables, name='compare_racktables'),
  url(r'^insight-jira/$', views.compare_insight_jira, name='compare_insight_jira'),
  url(r'^cloudamize-vs-device42/$', views.compare_cloudamize, name='compare_cloudamize'),
  url(r'^lansweeper-vs-device42-itam/$', views.compare_lansweeper, name='compare_lansweeper'),
  url(r'^glpi-vs-device42/$', views.compare_glpi, name='compare_glpi'),
  url(r'^netterrain-vs-device42/$', views.compare_netterrain, name='compare_netterrain'),
  url(r'^manageengine-vs-device42-itam/$', views.compare_manageengine, name='compare_manageengine'),
  url(r'^bluecat-vs-device42-ipam/$', views.compare_bluecat, name='compare_bluecat'),
  url(r'^idoit-vs-device42-cmdb/$', views.compare_idoit, name='compare_idoit'),
  url(r'^itop-vs-device42/$', views.compare_itop, name='compare_itop'),
  url(r'^phpipam-vs-device42/$', views.compare_phpipam, name='compare_phpipam'),
  url(r'^device42-vs-firescopeddm/$', views.compare_firescopeddm, name='compare_firescopeddm'),
  url(r'^cormant-cs/$', views.compare_cormant_cs, name='compare_cormant_cs')
]
