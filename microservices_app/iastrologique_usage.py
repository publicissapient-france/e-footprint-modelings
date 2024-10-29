import datetime

import pint
from efootprint.builders.hardware.storage_defaults import default_ssd
from efootprint.constants.sources import Sources
from efootprint.core.usage.usage_pattern import UsagePattern
from efootprint.core.usage.user_journey import UserJourney
from efootprint.core.usage.user_journey_step import UserJourneyStep
from efootprint.builders.hardware.devices_defaults import  default_laptop

from microservices_app.utils_iastrologique import create_job, create_job_with_template_dict, create_server, \
    create_hourly_usage_from_frequency, create_user_volume_for_usage_pattern

from efootprint.abstract_modeling_classes.source_objects import SourceValue
from efootprint.core.hardware.network import Network
from efootprint.core.system import System
from efootprint.constants.countries import Countries
from efootprint.constants.units import u

def iastrologique_modeling():
    start_date = datetime.datetime.strptime("2024-01-01", "%Y-%m-%d")

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

    hp_step_duration_per_trial_main_service = SourceValue(3*u.min, Sources.HYPOTHESIS)
    hp_step_duration_per_trial_eks = SourceValue(1*u.s, Sources.HYPOTHESIS)
    hp_step_duration_per_trial_main_pg = SourceValue(1*u.s, Sources.HYPOTHESIS)

    hp_step_duration_step = hp_step_duration_per_trial_main_service * nb_result_steps_trials + \
                                hp_step_duration_per_trial_eks * nb_result_steps_trials + \
                                hp_step_duration_per_trial_main_pg * nb_result_steps_trials

    hp_step_duration_step = hp_step_duration_step.set_label("Request duration step")

    result_step = UserJourneyStep(
        "Modeling result step", hp_step_duration_step,
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


    #Definiton of UserJourney
    iastrologique_user_journey = UserJourney(
        "IAstrologique user journey", [main_crm_step, result_step])
    jenkins_user_journey = UserJourney("Jenkins user journey", [jenkins_step])
    pdf_user_journey = UserJourney("PDF user journey", [pdf_retrieval_step, pdf_submission_step])
    pg_update_user_journey = UserJourney("Postgres Update user journey", [pg_update_step])
    pg_initial_download_user_journey = UserJourney("Postgres Initial Download user journey", [pg_initial_download_step])
    tracking_metrics_user_journey = UserJourney("Tracking metrics user journey", [tracking_metrics_step])

    #Network definition
    network = Network("Default network", SourceValue(0.05 * u("kWh/GB"), Sources.TRAFICOM_STUDY))

    #Device definition
    default_laptop_system = default_laptop()

    #definiton of UsagePattern
    jenkins_build_up = UsagePattern(
        "Jenkins Build UP",
        jenkins_user_journey,
        [default_laptop_system],
        network,
        Countries.FRANCE(),
        create_hourly_usage_from_frequency(
            1, start_date, pint.Unit(u.dimensionless), 'daily', 7*u.year, True, [9]
        )
    )

    iastrologique_pdf_up = UsagePattern(
        "Retrieve and submit pdf documents in IAstrologist in France on laptop",
        pdf_user_journey,
        [default_laptop_system],
        network,
        Countries.FRANCE(),
        create_user_volume_for_usage_pattern(
            'daily', False, list(range(10, 24)))
    )

    iastrologique_up = UsagePattern(
        "IAstrologique usage in France on laptop",
        iastrologique_user_journey,
        [default_laptop_system],
        network,
        Countries.FRANCE(),
        create_user_volume_for_usage_pattern(
                'daily', False, list(range(10, 24)), use_coefficient=True)
    )

    initialize_postgres_db_up = UsagePattern(
        "Initial download of the IAstrologique database",
        pg_initial_download_user_journey,
        [default_laptop_system],
        network,
        Countries.FRANCE(),
        create_hourly_usage_from_frequency(
            1, start_date, pint.Unit(u.dimensionless), 'yearly', 7*u.year, False, [1], [0]
        )
    )

    update_database_up = UsagePattern(
        "Monthly database update",
        pg_update_user_journey,
        [default_laptop_system],
        network,
        Countries.FRANCE(),
        create_hourly_usage_from_frequency(
            1, start_date, pint.Unit(u.dimensionless), 'monthly', 7*u.year, False, [1], [0]
        )
    )

    grafana_visualizing_metrics_up = UsagePattern(
        "One hour of KPI watching per day",
        tracking_metrics_user_journey,
        [default_laptop_system],
        network,
        Countries.FRANCE(),
        create_hourly_usage_from_frequency(
            1, start_date, pint.Unit(u.dimensionless), 'daily', 7*u.year, False, [10]
        )
    )

    system_iastrologique = System(
        "IAstrologique usage in 2024",
        [iastrologique_up, iastrologique_pdf_up, update_database_up, jenkins_build_up, initialize_postgres_db_up, grafana_visualizing_metrics_up]
    )

    return system_iastrologique

if __name__ == "__main__":
    system = iastrologique_modeling()
    iastrologique_up = system.usage_patterns[0]

    print(iastrologique_up)