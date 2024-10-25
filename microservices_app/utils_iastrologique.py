import os
import sys

from efootprint.core.hardware.servers.autoscaling import Autoscaling
from efootprint.core.usage.job import Job

from llm_modelings.bloom_efootprint import storage

sys.path.append(os.path.join("..", ".."))

from footprint_model.constants.sources import SourceValue, Sources
from footprint_model.core.user_journey import UserJourney, UserJourneyStep
from efootprint.core.hardware.storage import Storage
from efootprint.core.hardware.servers.autoscaling import Autoscaling
from footprint_model.core.usage_pattern import UsagePattern
from footprint_model.constants.countries import Countries
from footprint_model.constants.units import u
from footprint_model.utils.plot_emission_diffs import EmissionPlotter
from footprint_model.constants.explainable_quantities import ExplainableQuantity
from matplotlib import pyplot as plt

#hypothesis definition
#---------------------------------------------------------------------------
#STORAGE
#---------------------------------------------------------------------------
#The default capacity of a SSD is set to 1TB
#For a SSD of 1TB, the carbon footprint is set to 160 kgCO2eq
hp_ssd_capacity = SourceValue(1 * u.To, Sources.STORAGE_EMBODIED_CARBON_STUDY)
hp_ssd_carbon_footprint = SourceValue(160 * u.kg, Sources.STORAGE_EMBODIED_CARBON_STUDY)
#---------------------------------------------------------------------------
#SERVER
#---------------------------------------------------------------------------
#Definition of two instance configurations, one for large instances and one for small instances (for storage specifically)
#Use of an instance type variable to define easily the instance type
hp_instance_configuration = {
    "lg": {
        "carbon_footprint": SourceValue(1000 * u.kg, Sources.HYPOTHESIS),
        "power": SourceValue(300 * u.W, Sources.HYPOTHESIS),
        "idle_power": SourceValue(50 * u.W, Sources.HYPOTHESIS),
        "ram": SourceValue(256 * u.Go, Sources.USER_INPUT),
        "cpu": SourceValue(64 * u.core, Sources.USER_INPUT)
    },
    "sm": {
        "carbon_footprint": SourceValue(200 * u.kg, Sources.HYPOTHESIS),
        "power": SourceValue(150 * u.W, Sources.HYPOTHESIS),
        "idle_power": SourceValue(20 * u.W, Sources.HYPOTHESIS),
        "ram": SourceValue(32 * u.Go, Sources.USER_INPUT),
        "cpu": SourceValue(8 * u.core, Sources.USER_INPUT)
    }
}
#---------------------------------------------------------------------------
#JOB
#---------------------------------------------------------------------------
hp_job_type={
    "default": {
        "data_upload": SourceValue(10 * u.ko, Sources.HYPOTHESIS),
        "data_download": SourceValue(500 * u.ko, Sources.HYPOTHESIS),
        "data_stored": SourceValue(0 * u.ko, Sources.HYPOTHESIS),
        "request_duration": SourceValue(1 * u.s, Sources.HYPOTHESIS),
        "server_ram_needed": SourceValue(1, Sources.HYPOTHESIS),
        "cpu_needed": SourceValue(1, Sources.HYPOTHESIS)
    },
    "base_calcul_a": {
        "data_upload": SourceValue(10 * u.ko, Sources.HYPOTHESIS),
        "data_download": SourceValue(2 * u.mo, Sources.HYPOTHESIS),
        "data_stored": SourceValue(0 * u.ko, Sources.HYPOTHESIS),
        "request_duration": SourceValue(3 * u.s, Sources.HYPOTHESIS),
        "server_ram_needed": SourceValue(2, Sources.HYPOTHESIS),
        "cpu_needed": SourceValue(2, Sources.HYPOTHESIS)
    },
    "base_calcul_b": {
        "data_upload": SourceValue(0 * u.ko, Sources.HYPOTHESIS),
        "data_download": SourceValue(500 * u.mo, Sources.HYPOTHESIS),
        "data_stored": SourceValue(0 * u.ko, Sources.HYPOTHESIS),
        "request_duration": SourceValue(1 * u.s, Sources.HYPOTHESIS),
        "server_ram_needed": SourceValue(2, Sources.HYPOTHESIS),
        "cpu_needed": SourceValue(2, Sources.HYPOTHESIS)
    },
    "jenkins": {
        "data_upload": SourceValue(100 * u.ko, Sources.HYPOTHESIS),
        "data_download": SourceValue(100 * u.ko, Sources.HYPOTHESIS),
        "data_stored": SourceValue(0 * u.ko, Sources.HYPOTHESIS),
        "request_duration": SourceValue(1 * u.s, Sources.HYPOTHESIS),
        "server_ram_needed": SourceValue(1, Sources.HYPOTHESIS),
        "cpu_needed": SourceValue(1, Sources.HYPOTHESIS)
    }
}


#Util method to optimize the creation of storage and avoid multiple call of init Storage in the main script
def create_storage(name):
    return Storage(
        name=name,
        carbon_footprint_fabrication=SourceValue(hp_ssd_carbon_footprint * u.kg, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        power=SourceValue(1.3 * u.W, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        lifespan=SourceValue(6 * u.years, Sources.HYPOTHESIS),
        idle_power=SourceValue(0 * u.W, Sources.HYPOTHESIS),
        storage_capacity=hp_ssd_capacity,
        power_usage_effectiveness=SourceValue(1.2 * u.dimensionless, Sources.HYPOTHESIS),
        data_replication_factor=SourceValue(3* u.dimensionless, Sources.HYPOTHESIS),
        data_storage_duration=SourceValue(1 * u.year, Sources.HYPOTHESIS),
        base_storage_need=SourceValue(0 * u.Go, Sources.HYPOTHESIS),
        average_carbon_intensity=SourceValue(0.1 * u.kgCO2eq / u.kWh, Sources.HYPOTHESIS),
    )

def create_server(name, instance_type, serv_storage):
    return Autoscaling(
        name,
        carbon_footprint_fabrication=hp_instance_configuration[instance_type]["carbon_footprint"],
        power=hp_instance_configuration[instance_type]["power"],
        lifespan=SourceValue(6 * u.year, Sources.HYPOTHESIS),
        idle_power=hp_instance_configuration[instance_type]["idle_power"],
        ram=hp_instance_configuration[instance_type]["ram"],
        cpu_cores=hp_instance_configuration[instance_type]["cpu"],
        power_usage_effectiveness=SourceValue(1.2 * u.dimensionless, Sources.HYPOTHESIS),
        average_carbon_intensity=SourceValue(0.1 * u.kgCO2eq / u.kWh, Sources.HYPOTHESIS),
        server_utilization_rate=SourceValue(0.5 * u.dimensionless, Sources.HYPOTHESIS),
        base_ram_consumption=SourceValue(0.5 * u.Go, Sources.HYPOTHESIS),
        base_cpu_consumption=SourceValue(0.5 * u.core, Sources.HYPOTHESIS),
        storage=serv_storage
    )

def create_job(name, data_upload, data_download, data_stored, request_duration, ram_needed, cpu_needed, server,
        nb_result_step_trial=None):
    if nb_result_step_trial is not None:
        data_upload = data_upload * nb_result_step_trial
        data_download = data_download * nb_result_step_trial
        data_stored = data_stored * nb_result_step_trial
        request_duration = request_duration * nb_result_step_trial
    else :
        data_upload = SourceValue(data_upload, Sources.HYPOTHESIS)
        data_download = SourceValue(data_download, Sources.HYPOTHESIS)
        data_stored = SourceValue(data_stored, Sources.HYPOTHESIS)
        request_duration = SourceValue(request_duration, Sources.HYPOTHESIS)
    return Job(
        name=name,
        data_upload=data_upload,
        data_download=data_download,
        data_stored=data_stored,
        request_duration=request_duration,
        ram_needed=SourceValue(ram_needed, Sources.HYPOTHESIS),
        cpu_needed=SourceValue(cpu_needed, Sources.HYPOTHESIS),
        server=server
    )

def create_job_with_template_dict(name, job_template, server, nb_result_step_trial=None):
    data_upload = hp_job_type[job_template]["data_upload"]
    data_download = hp_job_type[job_template]["data_download"]
    data_stored = hp_job_type[job_template]["data_stored"]
    request_duration = hp_job_type[job_template]["request_duration"]
    if nb_result_step_trial is not None:
        data_upload = data_upload * nb_result_step_trial
        data_download = data_download * nb_result_step_trial
        data_stored = data_stored * nb_result_step_trial
        request_duration = request_duration * nb_result_step_trial
    return Job(
        name=name,
        data_upload=data_upload,
        data_download=data_download,
        data_stored=data_stored,
        request_duration=request_duration,
        ram_needed=hp_job_type[job_template]["server_ram_needed"],
        cpu_needed=hp_job_type[job_template]["cpu_needed"],
        server=server
    )


def create_user_journey_step(name, user_time_spent, job):
    return UserJourneyStep(
        name=name,
        job=job,
        user_time_spent=SourceValue(user_time_spent, Sources.HYPOTHESIS),
    )



def plot_from_system(emissions_dict__old, emissions_dict__new, title, filepath, figsize):
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize)

    EmissionPlotter(
        ax, emissions_dict__old, emissions_dict__new, title=title, rounding_value=1,
        timespan=ExplainableQuantity(1 * u.year, "one year")).plot_emission_diffs()
    plt.savefig(filepath)


def create_usage_pattern(journey_name, steps, device_population, network, uj_freq, time_interval):
    uj_steps = []
    for step in steps:
        step_name = step['step_name']
        request_service = step['request_service']
        data_upload = step['data_upload']
        data_download = step['data_download']
        request_duration = step['request_duration']
        server_ram = step['server_ram']
        step_duration = step['step_duration']

        step = UserJourneyStep(step_name, request_service, data_upload, data_download, step_duration, request_duration,
                               server_ram_per_data_transferred=server_ram)

        uj_steps.append(step)

    user_journey = UserJourney(journey_name, uj_steps=uj_steps)
    usage_pattern = UsagePattern(journey_name, user_journey, device_population, network, uj_freq, time_interval)

    return usage_pattern

