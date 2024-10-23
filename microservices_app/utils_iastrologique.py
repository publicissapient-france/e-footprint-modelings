import os
import sys

sys.path.append(os.path.join("..", ".."))

from footprint_model.constants.sources import SourceValue, Sources
from footprint_model.core.user_journey import UserJourney, UserJourneyStep
from footprint_model.core.server import Server
from footprint_model.core.storage import Storage
from footprint_model.core.usage_pattern import UsagePattern
from footprint_model.constants.countries import Countries
from footprint_model.constants.units import u
from footprint_model.utils.plot_emission_diffs import EmissionPlotter
from footprint_model.constants.explainable_quantities import ExplainableQuantity
from matplotlib import pyplot as plt


def plot_from_system(emissions_dict__old, emissions_dict__new, title, filepath, figsize):
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize)

    EmissionPlotter(
        ax, emissions_dict__old, emissions_dict__new, title=title, rounding_value=1,
        timespan=ExplainableQuantity(1 * u.year, "one year")).plot_emission_diffs()
    plt.savefig(filepath)


def create_server(name, carbon_footprint, power, idle_power, ram, cpu, cloud):
    return Server(
        name, carbon_footprint_fabrication=SourceValue(carbon_footprint * u.kg, Sources.HYPOTHESIS),
        power=SourceValue(power * u.W, Sources.HYPOTHESIS), lifespan=SourceValue(6 * u.year, Sources.HYPOTHESIS),
        idle_power=SourceValue(idle_power * u.W, Sources.HYPOTHESIS), ram=SourceValue(ram * u.Go, Sources.USER_INPUT),
        nb_of_cpus=cpu, power_usage_effectiveness=1.2, country=Countries.FRANCE, cloud=cloud)


def create_storage(name, carbon_footprint, storage):
    return Storage(
        name, carbon_footprint_fabrication=SourceValue(carbon_footprint * u.kg, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        power=SourceValue(1.3 * u.W, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        lifespan=SourceValue(6 * u.years, Sources.HYPOTHESIS), idle_power=SourceValue(0 * u.W, Sources.HYPOTHESIS),
        storage_capacity=SourceValue(storage * u.To, Sources.STORAGE_EMBODIED_CARBON_STUDY), power_usage_effectiveness=1.2,
        country=Countries.FRANCE, data_replication_factor=3)


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

