import os
import sys

from efootprint.builders.hardware.devices_defaults import default_laptop
from efootprint.builders.hardware.storage_defaults import default_ssd
from efootprint.constants.sources import Sources
from efootprint.core.usage.user_journey_step import UserJourneyStep

from microservices_app.utils_iastrologique import create_job, create_job_with_template_dict, create_server

sys.path.append(os.path.join("..", ".."))


from efootprint.abstract_modeling_classes.source_objects import SourceValue, SourceHourlyValues
from efootprint.core.hardware.network import Network as Networks
from efootprint.core.system import System
from efootprint.constants.countries import Countries
from efootprint.constants.units import u

import pandas as pd

#Storage definition
iastrologique_app_navigation_storage = default_ssd("iastrologique app navigation storage")
eks_navigation_storage = default_ssd("EKS navigation storage")
postgres_storage = default_ssd("Postgres storage")
mongodb_storage = default_ssd("MongoDB storage")
jenkins_storage = default_ssd("AWS storage")
salesforce_crm_storage = default_ssd("Salesforce CRM storage")
prometheus_storage = default_ssd("Prometheus Grafana storage")

#Server definition
# Web Application / MS
iastrologique_app_server = create_server(
    "iastrologique app server", "lg", iastrologique_app_navigation_storage)
eks_server = create_server("EKS server", "lg", eks_navigation_storage)
jenkins_server = create_server("Jenkins server", "lg", jenkins_storage)
salesforce_crm = create_server("Salesforce CRM", "lg", salesforce_crm_storage )
prometheus_server = create_server("Prometheus server", "lg", prometheus_storage)
postgres_server = create_server("postgres server", "sm", postgres_storage)
mongodb_server = create_server("MongoDB server", "sm", mongodb_storage)


#Job definition
nb_result_steps_trials = SourceValue(5*u.dimensionless, Sources.HYPOTHESIS)

jenkins_job = create_job_with_template_dict("Jenkins job", 'jenkins', jenkins_server)
salesforce_crm_data_fetch_job = create_job_with_template_dict(
    "Salesforce CRM Data Fetch", 'default', salesforce_crm)
iastrologique_data_fetch_pg_job = create_job_with_template_dict(
    "IAstrologique Data Fetch on Postgres", 'default', postgres_server)
mongodb_data_fetch_job = create_job_with_template_dict(
    "MongoDB Data Fetch", 'default', mongodb_server)
form_filling_job = create_job(
    "Form Filling",
    50*u.kB, 2*u.MB, 0*u.kB, 3*u.s, 2*u.GB, 1*u.core, iastrologique_app_server)

five_modeling_result_jobs = create_job_with_template_dict(
    '5 modeling result', 'base_calcul_a', iastrologique_app_server, nb_result_steps_trials)
five_bis_result_api_calls_jobs = create_job_with_template_dict(
    '5 bis result API calls', 'base_calcul_b', eks_server, nb_result_steps_trials)
five_ter_result_postgres_calls_jobs = create_job_with_template_dict(
    '5 ter result postgres calls', 'base_calcul_b', postgres_server, nb_result_steps_trials)

pdf_retrevial_job = create_job(
    "PDF retrieval", 10*u.kB, 200*u.kB, 0*u.kB, 1*u.s, 2*u.GB, 1*u.core, mongodb_server)

pdf_submission_job = create_job(
    "PDF submission", 200*u.kB, 10*u.kB, 200*u.kB, 1*u.s, 2*u.GB, 1*u.core, mongodb_server)

pg_update_step_job = create_job(
    "Postgres Update", 10*u.kB, 260*u.MB, 260*u.MB, 3*u.s, 2*u.GB, 2*u.core, postgres_server)

pg_initial_download_job = create_job(
    "Postgres Initial Download", 10*u.kB, 78*u.GB, 78*u.GB, 10*u.s, 1*u.GB, 1*u.core, postgres_server)

tracking_metrics_job = create_job(
    "Tracking metrics", 5*u.MB, 0*u.kB, 0*u.MB, 3*u.s, 1*u.GB, 1*u.core, prometheus_server
)

#UserJourney Step definiton
main_crm_step = UserJourneyStep(
    "Salesforce CRM step", SourceValue(5*u.min, Sources.HYPOTHESIS),
    [salesforce_crm_data_fetch_job,iastrologique_data_fetch_pg_job,mongodb_data_fetch_job,form_filling_job]
)

hp_request_duration_per_trial_main_service = SourceValue(3*u.min, Sources.HYPOTHESIS)
hp_request_duration_per_trial_eks = SourceValue(1*u.s, Sources.HYPOTHESIS)
hp_request_duration_per_trial_main_pg = SourceValue(1*u.s, Sources.HYPOTHESIS)

hp_request_duration_step = hp_request_duration_per_trial_main_service * nb_result_steps_trials + \
                            hp_request_duration_per_trial_eks * nb_result_steps_trials + \
                            hp_request_duration_per_trial_main_pg * nb_result_steps_trials

hp_request_duration_step = hp_request_duration_step.set_label("Request duration step")

result_step = UserJourneyStep(
    "Modeling result step", hp_request_duration_step,
    [five_modeling_result_jobs, five_bis_result_api_calls_jobs, five_ter_result_postgres_calls_jobs]
)

jenkins_step = UserJourneyStep(
    "Jenkins step", SourceValue(1*u.hour, Sources.HYPOTHESIS), [jenkins_job])
pdf_retrieval_step = UserJourneyStep(
    "PDF retrieval step", SourceValue(2*u.min, Sources.HYPOTHESIS), [pdf_retrevial_job])
pdf_submission_step = UserJourneyStep(
    "PDF submission step", SourceValue(2*u.min, Sources.HYPOTHESIS), [pdf_submission_job])
pg_update_step = UserJourneyStep(
    "Postgres Update step", SourceValue(1*u.min, Sources.HYPOTHESIS), [pg_update_step_job])
pg_initial_download_step = UserJourneyStep(
    "Postgres Initial Download step", SourceValue(2*u.min, Sources.HYPOTHESIS), [pg_initial_download_job])
tracking_metrics_step = UserJourneyStep(
    "Tracking metrics step", SourceValue(5*u.min, Sources.HYPOTHESIS), [tracking_metrics_job])



def iastrologique_yearly_modeling(nb_paid_users: int, nb_free_users: int, previous_year_system: System=None):
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
                           base_ram_consumption=300*u.Mo, base_cpu_consumption=1*u.core)

    eks_microservices = Service("EKS microservices", eks_server, eks_navigation_storage,
                                base_ram_consumption=300*u.Mo, base_cpu_consumption=1*u.core)

    postgres_db_service = Service("postgres database", postgres_server, postgres_storage,
                                  base_ram_consumption=300*u.Mo, base_cpu_consumption=1*u.core)
    mongodb_service = Service("mongodb database", mongodb_server, mongodb_storage, base_ram_consumption=300*u.Mo)
    pdf_retrieval_service = Service("PDF exchange", mongodb_server, mongodb_storage, base_ram_consumption=300*u.Mo,
                                    base_cpu_consumption=1*u.core)

    jenkins_build_service = Service("Jenkins weekly build", jenkins_server, jenkins_storage, base_ram_consumption=100*u.Mo,
                                    base_cpu_consumption=1*u.core)
    salesforce_crm_service = Service(
        "Salesforce CRM", salesforce_crm, salesforce_crm_storage, base_ram_consumption=100*u.Mo,
        base_cpu_consumption=1*u.core)
    prometheus_tracking_service = Service("Performance tracking", prometheus_grafana_server, mongodb_storage,
                                          base_ram_consumption=300*u.Mo, base_cpu_consumption=1*u.core)
    grafana_visualization_service = Service("Performance visualization", prometheus_grafana_server, mongodb_storage,
                                            base_ram_consumption=100*u.Mo, base_cpu_consumption=1*u.core)

    iastrologique_users_laptops = DevicePopulation(
        "French IAstrologique users on laptop", nb_paid_users + nb_free_users, Countries.FRANCE, [default_laptop()])

    cron_server_call_hardware = Hardware(
        "virtual cron server", SourceValue(0*u.kg, Sources.HYPOTHESIS), SourceValue(0*u.W, Sources.HYPOTHESIS),
        SourceValue(6*u.year, Sources.HYPOTHESIS), SourceValue(24*u.dimensionless, Sources.HYPOTHESIS))
    cron_server_call = DevicePopulation("cron server call", 1, Countries.FRANCE, [cron_server_call_hardware])

    iastrologique_use_network = Networks.WIFI_NETWORK

    # Jenkins build
    jenkins_steps = [
        {"step_name": "build step", "request_service": jenkins_build_service,
         "data_upload": 100*u.ko, "data_download": 100*u.ko, "request_duration": 1*u.s, "server_ram": 1,
         "step_duration": 1*u.hour}
    ]
    jenkins_build_up = create_usage_pattern("Five one hour jenkins build per week", jenkins_steps, cron_server_call,
                                            iastrologique_use_network, 260*u.user_journey / (u.user*u.year), [[9, 10]])

    # Data fetching and main user_journey
    main_steps = [
        {"step_name": "1 Salesforce CRM data fetch",
         "request_service": salesforce_crm_service, "data_upload": 10*u.ko, "data_download": 500*u.ko,
         "request_duration": 1*u.s, "server_ram": 1, "step_duration": 10*u.s},
        {"step_name": "2 IAstrologique data fetch on postgres",
         "request_service": postgres_db_service, "data_upload": 10*u.ko, "data_download": 500*u.ko,
         "request_duration": 1*u.s, "server_ram": 1, "step_duration": 10*u.s},
        {"step_name": "3 mongodb data fetch", "request_service": mongodb_service,
         "data_upload": 10*u.ko, "data_download": 500*u.ko, "request_duration": 1*u.s, "server_ram": 1,
         "step_duration": 10*u.s},
        {"step_name": "4 form filling", "request_service": main_service, "data_upload": 50*u.ko,
         "data_download": 2*u.Mo, "request_duration": 3*u.s, "server_ram": 2, "step_duration": 5*u.min},
    ]

    nb_result_steps_trials = 5
    common_result_steps = [{
        # user stories in mural https://app.mural.co/t/publicissapient7269/m/publicissapient7269/1689753725738/b1039790afd9c5dbb3a4a734ae5060f3fd178975?sender=u83c6a5b55c8b3a5e62910396
        "step_name": "5 modeling result", "request_service": main_service, "data_upload": nb_result_steps_trials*10*u.ko,
        "data_download": nb_result_steps_trials*2*u.Mo, "request_duration": nb_result_steps_trials*3*u.s,
        "server_ram": 2, "step_duration": nb_result_steps_trials*3*u.min
        },
        {
            # Results come from API calls (containers hosted in EKS cluster)
            "step_name": "5 bis result API calls", "request_service": eks_microservices,
            "data_upload": nb_result_steps_trials*0*u.ko, "data_download": nb_result_steps_trials*500*u.ko,
            "request_duration": nb_result_steps_trials*1*u.s, "server_ram": 2,
            "step_duration": nb_result_steps_trials*1*u.s
        },
        {
            # Potentially these API calls call the postgres database that records ML results.
            "step_name": "5 ter result postgres calls", "request_service": postgres_db_service,
            "data_upload": nb_result_steps_trials*0*u.ko, "data_download": nb_result_steps_trials*500*u.ko,
            "request_duration": nb_result_steps_trials*1*u.s, "server_ram": 2,
            "step_duration": nb_result_steps_trials*1*u.s
        }

    ]
    tracking_metrics_step = [
        {'step_name': '6 Tracking metrics', 'request_service': prometheus_tracking_service,
         'data_upload': 5*u.Mo, 'data_download': 0*u.ko, 'request_duration': 3*u.s, 'server_ram': 1,
         'step_duration': 3*u.s}]

    main_steps += common_result_steps + tracking_metrics_step

    iastrologique_usage_pattern = create_usage_pattern(
        "IAstrologique usage in France on laptop", main_steps, iastrologique_users_laptops,
        iastrologique_use_network,
        ((15*nb_paid_users + 2*nb_free_users) / (nb_paid_users + nb_free_users))
       *u.user_journey / (u.user*u.year),
        [[10, 23]])

    # pdf exchange
    # Not mandatory
    pdf_steps = [
        {'step_name': 'pdf retrieval', 'request_service': pdf_retrieval_service, 'data_upload': 10*u.ko,
         'data_download': 200*u.ko, 'request_duration': 1*u.s, 'server_ram': 2, 'step_duration': 2*u.min},
        {'step_name': 'pdf submission', 'request_service': pdf_retrieval_service,
         'data_upload': 200*u.ko, 'data_download': 10*u.ko, 'request_duration': 1*u.s, 'server_ram': 2,
         'step_duration': 2*u.min}
    ]

    iastrologique_up_pdf = create_usage_pattern(
        "Retrieve and submit pdf documents in IAstrologique in France on laptop", pdf_steps, iastrologique_users_laptops,
        iastrologique_use_network, 1*u.user_journey / (u.user*u.year), [[10, 23]])

    postgres_update_steps = [
        {'step_name': 'update', 'request_service': postgres_db_service, 'data_upload': 10*u.ko,
         'data_download': 260*u.Mo, 'request_duration': 3*u.s, 'server_ram': 2, 'step_duration': 1*u.min}]

    update_database_up = create_usage_pattern("Monthly database update", postgres_update_steps, cron_server_call,
                                              iastrologique_use_network, 12*u.user_journey / (u.user*u.year), [[0, 1]])

    # initial data download
    postgres_initial_download_steps = [
        {'step_name': 'database download', 'request_service': postgres_db_service,
         'data_upload': 10*u.ko, 'data_download': 78*u.Go, 'request_duration': 10*u.s, 'server_ram': 1,
         'step_duration': 2*u.min}]

    initial_postgres_db_download_up = create_usage_pattern(
        "Initial download of the IAstrologique database", postgres_initial_download_steps, cron_server_call, iastrologique_use_network,
        1*u.user_journey / (u.user*u.year), [[9, 10]])

    visualizing_metrics_steps = [
        {'step_name': 'Tracking metrics', 'request_service': grafana_visualization_service,
         'data_upload': 10*u.ko, 'data_download': 200*u.ko, 'request_duration': 1*u.s, 'server_ram': 1,
         'step_duration': 5*u.min}]

    grafana_visualizing_metrics_up = create_usage_pattern(
        "One hour of KPI watching per day", visualizing_metrics_steps, cron_server_call, iastrologique_use_network,
        365*u.user_journey / (u.user*u.year), [[10, 23]])

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
