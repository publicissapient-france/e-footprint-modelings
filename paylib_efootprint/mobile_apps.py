from efootprint.constants.countries import Countries
from efootprint.abstract_modeling_classes.source_objects import SourceValue, Sources, SourceObject
from efootprint.core.service import Service
from efootprint.core.usage.user_journey import UserJourney, UserJourneyStep
from efootprint.core.usage.job import Job
from efootprint.core.usage.usage_pattern import UsagePattern
from efootprint.core.hardware.device_population import DevicePopulation
from efootprint.constants.units import u
from efootprint.builders.hardware.servers_defaults import default_serverless
from efootprint.builders.hardware.storage_defaults import default_ssd
from efootprint.builders.hardware.devices_defaults import default_smartphone
from efootprint.builders.hardware.network_defaults import default_mobile_network
from on_premise_infrastructure import paylib_service
from mobile_app_download_rate_computations import average_paylib_app_download_rate_android, average_paylib_app_download_rate_iphone

android_phones = DevicePopulation("Android phones", nb_devices=SourceValue(1e6 * u.user), country=Countries.FRANCE(),
                                  devices=[default_smartphone()])
iphones = DevicePopulation("iPhones", nb_devices=SourceValue(1e6 * u.user), country=Countries.FRANCE(),
                           devices=[default_smartphone()])

store_servers = default_serverless("Android and Apple store servers")
store_storages = default_ssd("Android and Apple store SSD storages")

smartphone_stores = Service(
    "Android and Apple store", store_servers, store_storages,
    base_ram_consumption=SourceValue(300 * u.MB, Sources.HYPOTHESIS),
    base_cpu_consumption=SourceValue(2 * u.core, Sources.HYPOTHESIS))

uj_app_download_android = UserJourney(
    "Téléchargement application Android",
    uj_steps=[
        UserJourneyStep(
            "Téléchargement store Android",
            user_time_spent=SourceValue(30 * u.s / u.uj, Sources.USER_DATA),
            jobs=[
                Job("job téléchargement Android app", service=smartphone_stores,
                    data_upload=SourceValue(100 * u.kB / u.uj, Sources.USER_DATA),
                    data_download=SourceValue(25 * u.MB / u.uj, Sources.USER_DATA),
                    request_duration=SourceValue(30 * u.s, Sources.HYPOTHESIS),
                    cpu_needed=SourceValue(0.1 * u.core / u.user_journey),
                    ram_needed=SourceValue(30 * u.MB / u.user_journey))
            ]
        )])

network = default_mobile_network()

up_app_download_android = UsagePattern(
    "Usage Android app download", uj_app_download_android, android_phones,
    network, average_paylib_app_download_rate_android, SourceObject([[9, 17]]))


uj_app_download_iphone = UserJourney(
    "Téléchargement application iPhone",
    uj_steps=[
        UserJourneyStep(
            "Téléchargement store iPhone",
            user_time_spent=SourceValue(30 * u.s / u.uj, Sources.USER_DATA),
            jobs=[
                Job("Téléchargement iOS app", smartphone_stores,
                    data_upload=SourceValue(100 * u.kB / u.uj, Sources.USER_DATA),
                    data_download=SourceValue(32 * u.MB / u.uj, Sources.USER_DATA),
                    request_duration=SourceValue(30 * u.s, Sources.HYPOTHESIS),
                    cpu_needed=SourceValue(0.1 * u.core / u.user_journey),
                    ram_needed=SourceValue(30 * u.MB / u.user_journey))
                    ]
            )
         ])

up_app_download_iphone = UsagePattern(
    "Usage iPhone app download", uj_app_download_iphone, iphones,
    network, average_paylib_app_download_rate_iphone, SourceObject([[9, 17]]))

uj_app_usage_iphone_android = UserJourney(
    "Utilisation de l’application sur iPhone ou Android",
    uj_steps=[
        UserJourneyStep(
            "Utilisation application Paylib",
            user_time_spent=SourceValue(30 * u.s / u.uj, Sources.USER_DATA),
            jobs=[
                Job("Requêtes utilisation application Paylib",
                    paylib_service,
                    data_upload=SourceValue(100 * u.kB / u.uj, Sources.USER_DATA),
                    data_download=SourceValue(32 * u.MB / u.uj, Sources.USER_DATA),
                    request_duration=SourceValue(30 * u.s, Sources.HYPOTHESIS),
                    cpu_needed=SourceValue(0.1 * u.core / u.user_journey),
                    ram_needed=SourceValue(30 * u.MB / u.user_journey)
                )
            ]
        )])

up_app_usage_android = UsagePattern(
    "Usage Android app download", uj_app_usage_iphone_android, android_phones,
    network, SourceValue(2 * u.uj / (u.user * u.year)), SourceObject([[9, 22]]))

up_app_usage_iphone = UsagePattern(
    "Usage iPhone app download", uj_app_usage_iphone_android, iphones,
    network, SourceValue(2 * u.uj / (u.user * u.year)), SourceObject([[9, 22]]))
