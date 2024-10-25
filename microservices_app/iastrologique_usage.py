import os
import sys

from executing import Source

sys.path.append(os.path.join("..", ".."))

from footprint_model.constants.physical_elements import Hardware
from footprint_model.constants.sources import SourceValue, Sources
from footprint_model.core.service import Service
from footprint_model.core.device_population import DevicePopulation, Devices
from footprint_model.core.network import Networks
from footprint_model.core.system import System
from footprint_model.constants.countries import Countries
from footprint_model.constants.units import u
from footprint_model.constants.files import PROJECT_ROOT_PATH, create_folder

from use_cases.multiservice_app_carbon_case.utils_iastrologique import plot_from_system, create_server, create_storage, \
    create_usage_pattern

import pandas as pd

USE_CASE_PATH = os.path.join(PROJECT_ROOT_PATH, "use_cases", "multiservice_app_carbon_case")
PLOTS_PATH = create_folder(os.path.join(USE_CASE_PATH, "plots"))


#hypothesis definition

#The default capacity of a SSD is set to 1TB
#For a SSD of 1TB, the carbon footprint is set to 160 kgCO2eq
hp_ssd_capacity = SourceValue(1 * u.To, Sources.STORAGE_EMBODIED_CARBON_STUDY)
hp_ssd_carbon_footprint = SourceValue(160 * u.kg, Sources.STORAGE_EMBODIED_CARBON_STUDY)

#Storage definition
iastrologique_app_navigation_storage = create_storage(
    "iastrologique app navigation storage", carbon_footprint=hp_ssd_carbon_footprint, storage=hp_ssd_capacity)
eks_navigation_storage = create_storage(
    "EKS navigation storage", carbon_footprint=hp_ssd_carbon_footprint, storage=hp_ssd_capacity)
postgres_storage = create_storage(
    "Postgres storage", carbon_footprint=hp_ssd_carbon_footprint, storage_capacity=hp_ssd_capacity)
mongodb_storage = create_storage(
    "MongoDB storage", carbon_footprint=hp_ssd_carbon_footprint, storage_capacity=hp_ssd_capacity)
jenkins_storage = create_storage(
    "AWS storage", carbon_footprint=hp_ssd_carbon_footprint, storage_capacity=hp_ssd_capacity)
salesforce_crm_storage = create_storage(
    "Salesforce CRM storage", carbon_footprint=hp_ssd_carbon_footprint, storage_capacity=hp_ssd_capacity)
prometheus_grafana_storage = create_storage(
    "Prometheus Grafana storage", carbon_footprint=hp_ssd_carbon_footprint, storage_capacity=hp_ssd_capacity)



def iastrologique_yearly_modeling(nb_paid_users: int, nb_free_users: int, previous_year_system: System=None):
    # Web Application / MS
    iastrologique_app_server = create_server("iastrologique app server", carbon_footprint=1000, power=300, idle_power=50, ram=256,
                                         cpu=64, cloud="Autoscaling")

    # EKS microservice cluster
    eks_server = create_server("EKS server", carbon_footprint=1000, power=300, idle_power=50, ram=256,
                               cpu=64, cloud="Autoscaling")

    # AWS RDS
    postgres_server = create_server("postgres server", carbon_footprint=200, power=150, idle_power=20, ram=32, cpu=8,
                                    cloud="Autoscaling")

    mongodb_server = create_server("MongoDB server", carbon_footprint=200, power=150, idle_power=20, ram=32, cpu=8,
                                   cloud="Autoscaling")

    # Jenkins
    jenkins_server = create_server("Jenkins server", carbon_footprint=1000, power=300, idle_power=50, ram=256, cpu=64,
                                   cloud="Autoscaling")

    # Salesforce CRM
    salesforce_crm = create_server("Salesforce CRM", carbon_footprint=1000, power=300, idle_power=50, ram=256, cpu=64,
                                   cloud="Serverless")

    # Prometheus & Grafana
    prometheus_grafana_server = create_server("Prometheus server", carbon_footprint=1000, power=300, idle_power=50, ram=256,
                                              cpu=64, cloud="On premise")

    # Handling of previous year storages
    if previous_year_system is not None:
        for storage in [iastrologique_app_navigation_storage, eks_navigation_storage, postgres_storage, mongodb_storage,
                        jenkins_storage, salesforce_crm_storage]:
            previous_year_storage_need = previous_year_system.get_storage_by_name(
                storage.name).long_term_storage_required
            previous_year_storage_need.left_child = None
            previous_year_storage_need.right_child = None
            previous_year_storage_need.label = f"{storage.name} storage need from previous year"
            storage.storage_need_from_previous_year = previous_year_storage_need

    main_service = Service("iastrologique", iastrologique_app_server, iastrologique_app_navigation_storage,
                           base_ram_consumption=300 * u.Mo, base_cpu_consumption=1 * u.core)

    eks_microservices = Service("EKS microservices", eks_server, eks_navigation_storage,
                                base_ram_consumption=300 * u.Mo, base_cpu_consumption=1 * u.core)

    postgres_db_service = Service("postgres database", postgres_server, postgres_storage,
                                  base_ram_consumption=300 * u.Mo, base_cpu_consumption=1 * u.core)
    mongodb_service = Service("mongodb database", mongodb_server, mongodb_storage, base_ram_consumption=300 * u.Mo)
    pdf_retrieval_service = Service("PDF exchange", mongodb_server, mongodb_storage, base_ram_consumption=300 * u.Mo,
                                    base_cpu_consumption=1 * u.core)

    jenkins_build_service = Service("Jenkins weekly build", jenkins_server, jenkins_storage, base_ram_consumption=100 * u.Mo,
                                    base_cpu_consumption=1 * u.core)
    salesforce_crm_service = Service(
        "Salesforce CRM", salesforce_crm, salesforce_crm_storage, base_ram_consumption=100 * u.Mo,
        base_cpu_consumption=1 * u.core)
    prometheus_tracking_service = Service("Performance tracking", prometheus_grafana_server, mongodb_storage,
                                          base_ram_consumption=300 * u.Mo, base_cpu_consumption=1*u.core)
    grafana_visualization_service = Service("Performance visualization", prometheus_grafana_server, mongodb_storage,
                                            base_ram_consumption=100 * u.Mo, base_cpu_consumption=1 * u.core)

    iastrologique_users_laptops = DevicePopulation(
        "French IAstrologique users on laptop", nb_paid_users + nb_free_users, Countries.FRANCE, [Devices.LAPTOP])

    cron_server_call_hardware = Hardware(
        "virtual cron server", SourceValue(0 * u.kg, Sources.HYPOTHESIS), SourceValue(0 * u.W, Sources.HYPOTHESIS),
        SourceValue(6 * u.year, Sources.HYPOTHESIS), SourceValue(24 * u.dimensionless, Sources.HYPOTHESIS))
    cron_server_call = DevicePopulation("cron server call", 1, Countries.FRANCE, [cron_server_call_hardware])

    iastrologique_use_network = Networks.WIFI_NETWORK

    # Jenkins build
    jenkins_steps = [
        {"step_name": "build step", "request_service": jenkins_build_service,
         "data_upload": 100 * u.ko, "data_download": 100 * u.ko, "request_duration": 1 * u.s, "server_ram": 1,
         "step_duration": 1 * u.hour}
    ]
    jenkins_build_up = create_usage_pattern("Five one hour jenkins build per week", jenkins_steps, cron_server_call,
                                            iastrologique_use_network, 260 * u.user_journey / (u.user * u.year), [[9, 10]])

    # Data fetching and main user_journey
    main_steps = [
        {"step_name": "1 Salesforce CRM data fetch",
         "request_service": salesforce_crm_service, "data_upload": 10 * u.ko, "data_download": 500 * u.ko,
         "request_duration": 1 * u.s, "server_ram": 1, "step_duration": 10 * u.s},
        {"step_name": "2 IAstrologique data fetch on postgres",
         "request_service": postgres_db_service, "data_upload": 10 * u.ko, "data_download": 500 * u.ko,
         "request_duration": 1 * u.s, "server_ram": 1, "step_duration": 10 * u.s},
        {"step_name": "3 mongodb data fetch", "request_service": mongodb_service,
         "data_upload": 10 * u.ko, "data_download": 500 * u.ko, "request_duration": 1 * u.s, "server_ram": 1,
         "step_duration": 10 * u.s},
        {"step_name": "4 form filling", "request_service": main_service, "data_upload": 50 * u.ko,
         "data_download": 2 * u.Mo, "request_duration": 3 * u.s, "server_ram": 2, "step_duration": 5 * u.min},
    ]

    nb_result_steps_trials = 5
    common_result_steps = [{
        # user stories in mural https://app.mural.co/t/publicissapient7269/m/publicissapient7269/1689753725738/b1039790afd9c5dbb3a4a734ae5060f3fd178975?sender=u83c6a5b55c8b3a5e62910396
        "step_name": "5 modeling result", "request_service": main_service, "data_upload": nb_result_steps_trials * 10 * u.ko,
        "data_download": nb_result_steps_trials * 2 * u.Mo, "request_duration": nb_result_steps_trials * 3 * u.s,
        "server_ram": 2, "step_duration": nb_result_steps_trials * 3 * u.min
        },
        {
            # Results come from API calls (containers hosted in EKS cluster)
            "step_name": "5 bis result API calls", "request_service": eks_microservices,
            "data_upload": nb_result_steps_trials * 0 * u.ko, "data_download": nb_result_steps_trials * 500 * u.ko,
            "request_duration": nb_result_steps_trials * 1 * u.s, "server_ram": 2,
            "step_duration": nb_result_steps_trials * 1 * u.s
        },
        {
            # Potentially these API calls call the postgres database that records ML results.
            "step_name": "5 ter result postgres calls", "request_service": postgres_db_service,
            "data_upload": nb_result_steps_trials * 0 * u.ko, "data_download": nb_result_steps_trials * 500 * u.ko,
            "request_duration": nb_result_steps_trials * 1 * u.s, "server_ram": 2,
            "step_duration": nb_result_steps_trials * 1 * u.s
        }

    ]
    tracking_metrics_step = [
        {'step_name': '6 Tracking metrics', 'request_service': prometheus_tracking_service,
         'data_upload': 5 * u.Mo, 'data_download': 0 * u.ko, 'request_duration': 3 * u.s, 'server_ram': 1,
         'step_duration': 3 * u.s}]

    main_steps += common_result_steps + tracking_metrics_step

    iastrologique_usage_pattern = create_usage_pattern(
        "IAstrologique usage in France on laptop", main_steps, iastrologique_users_laptops,
        iastrologique_use_network,
        ((15 * nb_paid_users + 2 * nb_free_users) / (nb_paid_users + nb_free_users))
        * u.user_journey / (u.user * u.year),
        [[10, 23]])

    # pdf exchange
    # Not mandatory
    pdf_steps = [
        {'step_name': 'pdf retrieval', 'request_service': pdf_retrieval_service, 'data_upload': 10 * u.ko,
         'data_download': 200 * u.ko, 'request_duration': 1 * u.s, 'server_ram': 2, 'step_duration': 2 * u.min},
        {'step_name': 'pdf submission', 'request_service': pdf_retrieval_service,
         'data_upload': 200 * u.ko, 'data_download': 10 * u.ko, 'request_duration': 1 * u.s, 'server_ram': 2,
         'step_duration': 2 * u.min}
    ]

    iastrologique_up_pdf = create_usage_pattern(
        "Retrieve and submit pdf documents in IAstrologique in France on laptop", pdf_steps, iastrologique_users_laptops,
        iastrologique_use_network, 1 * u.user_journey / (u.user * u.year), [[10, 23]])

    postgres_update_steps = [
        {'step_name': 'update', 'request_service': postgres_db_service, 'data_upload': 10 * u.ko,
         'data_download': 260 * u.Mo, 'request_duration': 3 * u.s, 'server_ram': 2, 'step_duration': 1 * u.min}]

    update_database_up = create_usage_pattern("Monthly database update", postgres_update_steps, cron_server_call,
                                              iastrologique_use_network, 12 * u.user_journey / (u.user * u.year), [[0, 1]])

    # initial data download
    postgres_initial_download_steps = [
        {'step_name': 'database download', 'request_service': postgres_db_service,
         'data_upload': 10 * u.ko, 'data_download': 78 * u.Go, 'request_duration': 10 * u.s, 'server_ram': 1,
         'step_duration': 2 * u.min}]

    initial_postgres_db_download_up = create_usage_pattern(
        "Initial download of the IAstrologique database", postgres_initial_download_steps, cron_server_call, iastrologique_use_network,
        1 * u.user_journey / (u.user * u.year), [[9, 10]])

    visualizing_metrics_steps = [
        {'step_name': 'Tracking metrics', 'request_service': grafana_visualization_service,
         'data_upload': 10 * u.ko, 'data_download': 200 * u.ko, 'request_duration': 1 * u.s, 'server_ram': 1,
         'step_duration': 5 * u.min}]

    grafana_visualizing_metrics_up = create_usage_pattern(
        "One hour of KPI watching per day", visualizing_metrics_steps, cron_server_call, iastrologique_use_network,
        365 * u.user_journey / (u.user * u.year), [[10, 23]])

    iastrologique_system = System(
        "IAstrologique usage in 2024",
        [iastrologique_usage_pattern, iastrologique_up_pdf, update_database_up, jenkins_build_up,
         grafana_visualizing_metrics_up, initial_postgres_db_download_up])

    return iastrologique_system


if __name__ == "__main__":
    yearly_usage_df = pd.read_csv(os.path.join(USE_CASE_PATH, "yearly_nb_of_users.csv"))
    for i in range(len(yearly_usage_df)):
        year = yearly_usage_df["year"].iloc[i]
        nb_paid_users_that_year = yearly_usage_df["nb_paid_users"].iloc[i]
        nb_free_users_that_year = yearly_usage_df["nb_free_users"].iloc[i]

        iastrologique_system = iastrologique_yearly_modeling(nb_paid_users_that_year, nb_free_users_that_year)

        emissions_dict = [iastrologique_system.energy_footprints(), iastrologique_system.fabrication_footprints()]

        plot_from_system(
            emissions_dict, emissions_dict, "IAstrologique modeling", os.path.join(PLOTS_PATH, f"iastrologique_{year}.png"),
            (12, 8))

# TODO: refine server impacts thanks to BoaviztAPI
# TODO: be clear about dev preprod prod.
# TODO: for mongodb each time we see a new address we call the IAstrologique API and save it in MongoDB.
# TODO: modélisation des développeurs.
# TODO: modélisation ML. Pour l’instant en local. Ensuite il utilisera l’environnement AWS de dev.
