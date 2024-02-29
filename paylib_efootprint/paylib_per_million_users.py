from mobile_apps import up_app_download_iphone, up_app_download_android, up_app_usage_android, up_app_usage_iphone
from on_premise_infrastructure import preprod_up
from websites import up_site_recup, up_site_vitrine

from efootprint.core.system import System

paylib = System(
    "Paylib per million users",
    [up_site_recup, up_site_vitrine, preprod_up, up_app_download_iphone, up_app_download_android,
     up_app_usage_android, up_app_usage_iphone])

paylib.object_relationship_graph_to_file()
