from on_premise_infrastructure import site_recup, site_vitrine

from efootprint.constants.countries import Countries
from efootprint.abstract_modeling_classes.source_objects import SourceValue, Sources, SourceObject
from efootprint.core.hardware.device_population import DevicePopulation
from efootprint.core.hardware.network import Network
from efootprint.core.usage.usage_pattern import UsagePattern
from efootprint.core.usage.user_journey import UserJourney, UserJourneyStep
from efootprint.builders.hardware.devices_defaults import default_smartphone
from efootprint.constants.units import u


POPULATION = DevicePopulation("one million users", SourceValue(1e6 * u.user), Countries.FRANCE(), [default_smartphone()])

# In reality 98% smartphones
uj_recup = UserJourney("Visite site de récupération de fonds", uj_steps=[UserJourneyStep(
    "Parcours site récup", site_recup, SourceValue(100 * u.kB / u.uj, Sources.USER_DATA),
    SourceValue(1.1 * u.MB / u.uj, Sources.USER_DATA),
    user_time_spent=SourceValue(2 * u.min / u.uj, Sources.USER_DATA),
    request_duration=SourceValue(1.5 * u.s, Sources.HYPOTHESIS))])

network = Network("4G network", SourceValue(0.12 * u("kWh/GB"), Sources.TRAFICOM_STUDY))

up_site_recup = UsagePattern(
    "Site de récupération de fonds", uj_recup, POPULATION,
    network, SourceValue(1 * u.user_journey / (u.user * u.year), Sources.USER_DATA),
    SourceObject([[9, 17]]))

uj_vitrine = UserJourney("Visite site vitrine Paylib", uj_steps=[UserJourneyStep(
    "Parcours site vitrine", site_vitrine, SourceValue(100 * u.kB / u.uj, Sources.USER_DATA),
    SourceValue(7 * u.MB / u.uj, Sources.USER_DATA),
    user_time_spent=SourceValue(1.33 * u.min / u.uj, Sources.USER_DATA),
    request_duration=SourceValue(2.5 * u.s, Sources.HYPOTHESIS))])

# In reality 0.87% smartphones
up_site_vitrine = UsagePattern(
    "Usage site vitrine", uj_vitrine, POPULATION,
    network, SourceValue(1 * u.user_journey / (u.user * u.year), Sources.USER_DATA),
    SourceObject([[9, 17]]))
