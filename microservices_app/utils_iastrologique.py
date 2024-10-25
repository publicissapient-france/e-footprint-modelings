import os
import sys

from efootprint.builders.hardware.servers_defaults import default_autoscaling
from efootprint.builders.hardware.storage_defaults import default_ssd
from efootprint.core.usage.job import Job


sys.path.append(os.path.join("..", ".."))
from efootprint.abstract_modeling_classes.explainable_objects import ExplainableQuantity
from efootprint.abstract_modeling_classes.source_objects import SourceValue, Sources
from efootprint.core.hardware.servers.autoscaling import Autoscaling
from efootprint.core.usage.user_journey import UserJourney
from efootprint.core.usage.user_journey_step import UserJourneyStep
from efootprint.core.usage.usage_pattern import UsagePattern
from efootprint.constants.units import u

from efootprint.utils.plot_emission_diffs import EmissionPlotter

from matplotlib import pyplot as plt

#hypothesis definition
#---------------------------------------------------------------------------
#STORAGE
#---------------------------------------------------------------------------
#The default capacity of a SSD is set to 1TB
#---------------------------------------------------------------------------
#SERVER
#---------------------------------------------------------------------------
#Definition of two instance configurations, one for large instances and one for small instances (for storage specifically)
#Use of an instance type variable to define easily the instance type
hp_instance_configuration = {
    "lg": {
        "carbon_footprint_fabrication": SourceValue(1000 * u.kg, Sources.HYPOTHESIS),
        "power": SourceValue(300 * u.W, Sources.HYPOTHESIS),
        "idle_power": SourceValue(50 * u.W, Sources.HYPOTHESIS),
        "ram": SourceValue(256 * u.GB, Sources.USER_DATA),
        "cpu_cores": SourceValue(64 * u.core, Sources.USER_DATA)
    },
    "sm": {
        "carbon_footprint_fabrication": SourceValue(200 * u.kg, Sources.HYPOTHESIS),
        "power": SourceValue(150 * u.W, Sources.HYPOTHESIS),
        "idle_power": SourceValue(20 * u.W, Sources.HYPOTHESIS),
        "ram": SourceValue(32 * u.GB, Sources.USER_DATA),
        "cpu_cores": SourceValue(8 * u.core, Sources.USER_DATA)
    }
}
#---------------------------------------------------------------------------
#JOB
#---------------------------------------------------------------------------
hp_job_type={
    "default": {
        "data_upload": SourceValue(10 * u.kB, Sources.HYPOTHESIS),
        "data_download": SourceValue(500 * u.kB, Sources.HYPOTHESIS),
        "data_stored": SourceValue(0 * u.kB, Sources.HYPOTHESIS),
        "request_duration": SourceValue(1 * u.s, Sources.HYPOTHESIS),
        "server_ram_needed": SourceValue(1*u.GB, Sources.HYPOTHESIS),
        "cpu_needed": SourceValue(1*u.core, Sources.HYPOTHESIS)
    },
    "base_calcul_a": {
        "data_upload": SourceValue(10 * u.kB, Sources.HYPOTHESIS),
        "data_download": SourceValue(2 * u.MB, Sources.HYPOTHESIS),
        "data_stored": SourceValue(0 * u.kB, Sources.HYPOTHESIS),
        "request_duration": SourceValue(3 * u.s, Sources.HYPOTHESIS),
        "server_ram_needed": SourceValue(2*u.GB, Sources.HYPOTHESIS),
        "cpu_needed": SourceValue(2*u.core, Sources.HYPOTHESIS)
    },
    "base_calcul_b": {
        "data_upload": SourceValue(0 * u.kB, Sources.HYPOTHESIS),
        "data_download": SourceValue(500 * u.MB, Sources.HYPOTHESIS),
        "data_stored": SourceValue(0 * u.kB, Sources.HYPOTHESIS),
        "request_duration": SourceValue(1 * u.s, Sources.HYPOTHESIS),
        "server_ram_needed": SourceValue(2*u.GB, Sources.HYPOTHESIS),
        "cpu_needed": SourceValue(2*u.core, Sources.HYPOTHESIS)
    },
    "jenkins": {
        "data_upload": SourceValue(100 * u.kB, Sources.HYPOTHESIS),
        "data_download": SourceValue(100 * u.kB, Sources.HYPOTHESIS),
        "data_stored": SourceValue(0 * u.kB, Sources.HYPOTHESIS),
        "request_duration": SourceValue(1 * u.s, Sources.HYPOTHESIS),
        "server_ram_needed": SourceValue(1*u.GB, Sources.HYPOTHESIS),
        "cpu_needed": SourceValue(1*u.core, Sources.HYPOTHESIS)
    }
}


#Util method to optimize the creation of storage and avoid multiple call of init Storage in the main script
def create_storage(name):
    return default_ssd(name=name)

def create_server(name, instance_type, serv_storage):
    server_conf =hp_instance_configuration[instance_type]
    return default_autoscaling(name, **server_conf, storage=serv_storage)


def create_server_save(name, instance_type, serv_storage):
    return Autoscaling(
        name,
        carbon_footprint_fabrication=hp_instance_configuration[instance_type]["carbon_footprint"],
        power=hp_instance_configuration[instance_type]["power"],
        lifespan=SourceValue(6 * u.year, Sources.HYPOTHESIS),
        idle_power=hp_instance_configuration[instance_type]["idle_power"],
        ram=hp_instance_configuration[instance_type]["ram"],
        cpu_cores=hp_instance_configuration[instance_type]["cpu"],
        power_usage_effectiveness=SourceValue(1.2 * u.dimensionless, Sources.HYPOTHESIS),
        average_carbon_intensity=SourceValue(100 * u.g / u.kWh, Sources.HYPOTHESIS),
        server_utilization_rate=SourceValue(0.5 * u.dimensionless, Sources.HYPOTHESIS),
        base_ram_consumption=SourceValue(0.5 * u.GB, Sources.HYPOTHESIS),
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

