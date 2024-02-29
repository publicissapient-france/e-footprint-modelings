from efootprint.constants.countries import Countries
from efootprint.constants.sources import Sources
from efootprint.abstract_modeling_classes.source_objects import SourceValue, SourceObject
from efootprint.core.hardware.device_population import DevicePopulation
from efootprint.core.hardware.storage import Storage
from efootprint.core.service import Service
from efootprint.core.usage.usage_pattern import UsagePattern
from efootprint.core.usage.user_journey import UserJourney, UserJourneyStep
from efootprint.builders.hardware.servers_boaviztapi import on_premise_server_from_config
from efootprint.builders.hardware.devices_defaults import default_laptop
from efootprint.builders.hardware.network_defaults import default_wifi_network
from efootprint.constants.units import u

preprod_compute = on_premise_server_from_config(
    "Preprod compute", nb_of_cpu_units=2, nb_of_cores_per_cpu_unit=24, nb_of_ram_units=2,
    ram_quantity_per_unit_in_gb=128, average_carbon_intensity=SourceValue(100 * u.g / u.kWh, Sources.HYPOTHESIS),
    fixed_nb_of_instances=SourceValue(2 * u.dimensionless)
    )


preprod_storage = Storage(
        "Preprod storage",
        carbon_footprint_fabrication=SourceValue(160 * u.kg, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        power=SourceValue(1.3 * u.W, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        lifespan=SourceValue(6 * u.years, Sources.HYPOTHESIS),
        idle_power=SourceValue(0 * u.W, Sources.HYPOTHESIS),
        storage_capacity=SourceValue(1 * u.TB, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        power_usage_effectiveness=SourceValue(1.2 * u.dimensionless, Sources.HYPOTHESIS),
        average_carbon_intensity=SourceValue(100 * u.g / u.kWh),
        data_replication_factor=SourceValue(3 * u.dimensionless, Sources.HYPOTHESIS),
        storage_need_from_previous_year=SourceValue(12 * u.TB)
    )

preprod_service = Service(
    "Preprod", preprod_compute, preprod_storage,
    base_cpu_consumption=SourceValue(1 * u.core), base_ram_consumption=SourceValue(1 * u.GB))


preprod_uj = UserJourney("Preprod UJ", uj_steps=[
    UserJourneyStep("daily usage of preprod", preprod_service, data_download=SourceValue(1 * u.GB / u.uj),
                    data_upload=SourceValue(0 * u.GB / u.uj), user_time_spent=SourceValue(7 * u.hour / u.uj),
                    request_duration=SourceValue(16 * u.hour), cpu_needed=SourceValue(5 * u.core / u.uj),
                    ram_needed=SourceValue(1 * u.GB / u.uj))])


device_population = DevicePopulation("One laptop", nb_devices=SourceValue(1 * u.user),
                                     country=Countries.FRANCE(), devices=[default_laptop()])

preprod_up = UsagePattern("Preprod UP", preprod_uj, device_population, default_wifi_network(),
                              user_journey_freq_per_user=SourceValue(1 * u.uj / (u.user * u.day)),
                              time_intervals=SourceObject([[2, 18]]))

prod_compute = on_premise_server_from_config(
    "Prod compute", nb_of_cpu_units=2, nb_of_cores_per_cpu_unit=24, nb_of_ram_units=2,
    ram_quantity_per_unit_in_gb=128, average_carbon_intensity=SourceValue(100 * u.g / u.kWh, Sources.HYPOTHESIS),
    fixed_nb_of_instances=SourceValue(2 * u.dimensionless)
    )

prod_storage = Storage(
        "Prod storage",
        carbon_footprint_fabrication=SourceValue(160 * u.kg, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        power=SourceValue(1.3 * u.W, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        lifespan=SourceValue(6 * u.years, Sources.HYPOTHESIS),
        idle_power=SourceValue(0 * u.W, Sources.HYPOTHESIS),
        storage_capacity=SourceValue(1 * u.TB, Sources.STORAGE_EMBODIED_CARBON_STUDY),
        power_usage_effectiveness=SourceValue(1.2 * u.dimensionless, Sources.HYPOTHESIS),
        average_carbon_intensity=SourceValue(100 * u.g / u.kWh),
        data_replication_factor=SourceValue(3 * u.dimensionless, Sources.HYPOTHESIS),
        storage_need_from_previous_year=SourceValue(0 * u.TB)
    )

site_vitrine = Service(
    "Site vitrine Paylib", prod_compute, prod_storage,
    base_ram_consumption=SourceValue(300 * u.MB, Sources.HYPOTHESIS),
    base_cpu_consumption=SourceValue(2 * u.core, Sources.HYPOTHESIS))

site_recup = Service(
    "Usage site de récupération de fonds Paylib", prod_compute, prod_storage,
    base_ram_consumption=SourceValue(300 * u.MB, Sources.HYPOTHESIS),
    base_cpu_consumption=SourceValue(2 * u.core, Sources.HYPOTHESIS))

paylib_service = Service(
    "Paylib service", prod_compute, prod_storage,
    base_ram_consumption=SourceValue(1000 * u.MB, Sources.HYPOTHESIS),
    base_cpu_consumption=SourceValue(2 * u.core, Sources.HYPOTHESIS))
