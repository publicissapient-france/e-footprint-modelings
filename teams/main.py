import datetime
import pint
import sys

from efootprint.abstract_modeling_classes.explainable_object_base_class import Source
from efootprint.abstract_modeling_classes.source_objects import SourceValue
from efootprint.api_utils.system_to_json import system_to_json
from efootprint.builders.hardware.devices_defaults import default_laptop
from efootprint.builders.hardware.storage_defaults import default_ssd
from efootprint.constants.countries import Countries
from efootprint.constants.sources import Sources
from efootprint.core.hardware.network import Network
from efootprint.core.hardware.servers.on_premise import OnPremise
from efootprint.core.hardware.servers.serverless import Serverless
from efootprint.core.system import System
from efootprint.core.usage.job import Job
from efootprint.core.usage.usage_pattern import UsagePattern
from efootprint.core.usage.user_journey import UserJourney
from efootprint.core.usage.user_journey_step import UserJourneyStep
from efootprint.builders.time_builders import create_hourly_usage_from_daily_volume_and_list_of_hours, \
    create_hourly_usage_from_frequency
from efootprint.constants.units import u

sys.path.append("..")
from ai_use_case.builder.ecologits_builder import GenAIModel

# Define start date and base parameters such as daily visits or task execution frequency
start_date = datetime.datetime.strptime("2025-01-01", "%Y-%m-%d")
base_daily_nb_of_visits = 1000
pint_unit = pint.Unit(u.dimensionless)
frequency = 'monthly'
modeling_timespan = 1 * u.year
active_hours = [9, 10, 11, 14, 15, 16, 17]

# Assumptions defined as SourceValues to be visible in calculation graphs for better understanding of results
hypothesis_token_per_word = SourceValue(3 * u.dimensionless, Sources.HYPOTHESIS, "number of tokens per word")
hypothesis_nb_docs_ingested = SourceValue(
    1000 * u.dimensionless, Sources.HYPOTHESIS, "monthly number of documents ingested for RAG")
hypothesis_word_per_chat = SourceValue(500 * u.dimensionless, Sources.HYPOTHESIS, "number of words generated per chat")
hypothesis_word_per_document = SourceValue(
    2000 * u.dimensionless, Sources.HYPOTHESIS, "number of words per uploaded document")

# With assumptions defined, calculate tokens per chat, per document, tokens for RAG usage, and tokens for RAG loading
hypothesis_token_per_simple_chat = hypothesis_word_per_chat * hypothesis_token_per_word
hypothesis_token_per_chat_on_a_document = hypothesis_word_per_document * hypothesis_token_per_word
hypothesis_token_on_use_of_rag = (
        hypothesis_word_per_chat + hypothesis_word_per_document) * hypothesis_token_per_word
hypothesis_nb_token_to_fill_rag = (
        hypothesis_word_per_document * hypothesis_nb_docs_ingested * hypothesis_token_per_word)

# Define sources for resource consumption values for servers and GPUs
bloom_paper_source = Source("Estimating the Carbon Footprint of BLOOM", "https://arxiv.org/abs/2211.05100")
gpu_lifetime = SourceValue(6 * u.year, bloom_paper_source, "gpu_lifetime")
gpu_power = SourceValue(400 * u.W, bloom_paper_source, "GPU Power")
gpu_idle_power = SourceValue(50 * u.W, bloom_paper_source, "GPU idle power")
NB_OF_GPU_PER_INSTANCE = SourceValue(4 * u.dimensionless, Sources.USER_DATA, label="Number of GPUs")
RAM_PER_GPU = SourceValue(80 * u.GB, bloom_paper_source, label="RAM per GPU")
carbon_footprint_fabrication_server_without_gpu = SourceValue(
    2500 * u.kg, bloom_paper_source, "Carbon footprint without GPU")
carbon_footprint_fabrication_one_gpu = SourceValue(150 * u.kg, bloom_paper_source, "Carbon footprint one GPU")

cpu_core_per_gpu = SourceValue(1 * u.core, label="1 CPU core / GPU")

# With assumptions and sources defined and initial calculations done, we can define the other elements of our system.
# To understand interactions between objects, refer to efootprint documentation: https://boavizta.github.io/e-footprint/
# Define web servers and GPUs as OnPremise, i.e., without autoscaling
server_web = Serverless(
    "Teams server",
    carbon_footprint_fabrication=SourceValue(600 * u.kg, Sources.BASE_ADEME_V19),
    power=SourceValue(300 * u.W, Sources.HYPOTHESIS),
    lifespan=SourceValue(6 * u.year, Sources.HYPOTHESIS),
    idle_power=SourceValue(50 * u.W, Sources.HYPOTHESIS),
    ram=SourceValue(128 * u.GB, Sources.HYPOTHESIS),
    cpu_cores=SourceValue(4 * u.core, Sources.HYPOTHESIS),
    power_usage_effectiveness=SourceValue(1.2 * u.dimensionless, Sources.HYPOTHESIS),
    average_carbon_intensity=SourceValue(100 * u.g / u.kWh, Sources.HYPOTHESIS),
    server_utilization_rate=SourceValue(1 * u.dimensionless, Sources.HYPOTHESIS),
    base_ram_consumption=SourceValue(300 * u.MB, Sources.HYPOTHESIS),
    base_cpu_consumption=SourceValue(2 * u.core, Sources.HYPOTHESIS),
    storage=default_ssd(
        data_storage_duration=SourceValue(5 * u.year, Sources.HYPOTHESIS),
        data_replication_factor=SourceValue(2 * u.dimensionless, Sources.HYPOTHESIS),
        base_storage_need=SourceValue(200 * u.GB))
)

gpu_server = Serverless(
    "GPU server",
    carbon_footprint_fabrication=(
            carbon_footprint_fabrication_server_without_gpu + NB_OF_GPU_PER_INSTANCE * carbon_footprint_fabrication_one_gpu
        ).set_label("default"),
    power=(gpu_power * NB_OF_GPU_PER_INSTANCE).set_label("default"),
    lifespan=SourceValue(6 * u.year, Sources.HYPOTHESIS),
    idle_power=(gpu_idle_power * NB_OF_GPU_PER_INSTANCE).set_label("default"),
    ram=(RAM_PER_GPU * NB_OF_GPU_PER_INSTANCE).set_label("default"),
    cpu_cores=(NB_OF_GPU_PER_INSTANCE * cpu_core_per_gpu).set_label("default"),
    power_usage_effectiveness=SourceValue(1.2 * u.dimensionless, Sources.HYPOTHESIS),
    average_carbon_intensity=SourceValue(57 * u.g / u.kWh, Sources.HYPOTHESIS),
    server_utilization_rate=SourceValue(1 * u.dimensionless, Sources.USER_DATA),
    base_cpu_consumption=SourceValue(0 * u.core, Sources.HYPOTHESIS),
    base_ram_consumption=SourceValue(0 * u.GB, Sources.HYPOTHESIS),
    storage=default_ssd(
        data_storage_duration=SourceValue(5 * u.year, Sources.HYPOTHESIS),
        data_replication_factor=SourceValue(2 * u.dimensionless, Sources.HYPOTHESIS),
        base_storage_need=SourceValue(200 * u.GB))
)

# Define tasks to perform at each user journey step and server resource values
job_login = Job(
    "login",
    server=server_web,
    data_upload=SourceValue(5 * u.MB, Sources.HYPOTHESIS),
    data_download=SourceValue(2 * u.MB, Sources.HYPOTHESIS),
    data_stored=SourceValue(0 * u.MB, Sources.HYPOTHESIS),
    request_duration=SourceValue(2 * u.second, Sources.HYPOTHESIS),
    cpu_needed=SourceValue(0.2 * u.core, Sources.HYPOTHESIS),
    ram_needed=SourceValue(0.2 * u.GB, Sources.HYPOTHESIS)
)

# Define text generation models for different tasks
meta_llama = GenAIModel("openai", "gpt-4o", gpu_server)

job_doc_chat = meta_llama.job(hypothesis_token_per_chat_on_a_document)

# Define different steps in the user journey and tasks for each step
login_step = UserJourneyStep(
    "login_step",
    jobs=[job_login],
    user_time_spent=SourceValue(30 * u.second, Sources.HYPOTHESIS)
)
chat_simple_step = UserJourneyStep(
    "chat_simple_step",
    jobs=[job_simple_chat],
    user_time_spent=SourceValue(5 * u.minute, Sources.HYPOTHESIS)
)
chat_doc_step = UserJourneyStep(
    "chat_doc_step",
    jobs=[job_doc_chat],
    user_time_spent=SourceValue(10 * u.minute, Sources.HYPOTHESIS)
)
use_rag_step = UserJourneyStep(
    "use_rag_step",
    jobs=[job_use_rag],
    user_time_spent=SourceValue(5 * u.minute, Sources.HYPOTHESIS)
)
fill_rag_step = UserJourneyStep(
    "fill_rag_step",
    jobs=[job_fill_rag],
    user_time_spent=SourceValue(1 * u.hour, Sources.HYPOTHESIS)
)

# Definition of the different user journeys to be performed. In this case, we simplify the example by
# reducing the analysis to four different user journeys with the minimum possible steps.
user_journey_chat_with_simple_bot = UserJourney(
    "user_journey_chat_with_simple_bot",
    uj_steps=[login_step, chat_simple_step]
)

user_journey_chat_with_advanced_bot = UserJourney(
    "user_journey_chat_with_advanced_bot",
    uj_steps=[login_step, chat_doc_step]
)

user_journey_use_rag = UserJourney(
    "user_journey_use_rag",
    uj_steps=[login_step, use_rag_step]
)

user_journey_fill_rag = UserJourney(
    "user_journey_fill_rag",
    uj_steps=[fill_rag_step]
)

# Definition of the network used for the different tasks.
network = Network(
        "WIFI network",
        bandwidth_energy_intensity=SourceValue(0.05 * u("kWh/GB"), Sources.TRAFICOM_STUDY))

# Definition of the type of device used for the different tasks.
default_laptop = default_laptop()

# In the second-to-last step, define the different usage patterns for each user journey.
# For each usage pattern, define the user journey, the device used, the network used, the country,
# and the time-based usage.
usage_pattern_simple = UsagePattern(
    "chat_with_simple_bot",
    user_journey_chat_with_simple_bot,
    [default_laptop],
    network,
    Countries.FRANCE(),
    create_hourly_usage_from_daily_volume_and_list_of_hours(
        modeling_timespan, round(base_daily_nb_of_visits * 0.56, 0), active_hours, start_date, pint_unit)
)

usage_pattern_advanced = UsagePattern(
    "chat_with_advanced_bot",
    user_journey_chat_with_advanced_bot,
    [default_laptop],
    network,
    Countries.FRANCE(),
    create_hourly_usage_from_daily_volume_and_list_of_hours(
        modeling_timespan, round(base_daily_nb_of_visits * 0.27, 0), active_hours, start_date, pint_unit)
)

usage_pattern_use_rag = UsagePattern(
    "use_rag",
    user_journey_use_rag,
    [default_laptop],
    network,
    Countries.FRANCE(),
    create_hourly_usage_from_daily_volume_and_list_of_hours(
        modeling_timespan, round(base_daily_nb_of_visits * 0.17, 0), active_hours, start_date, pint_unit)
)

usage_pattern_fill_rag = UsagePattern(
    "fill_rag",
    user_journey_fill_rag,
    [default_laptop],
    network,
    Countries.FRANCE(),
    create_hourly_usage_from_frequency(
        modeling_timespan, 1, frequency, active_days=[1], start_date=start_date, pint_unit=pint_unit)
)

# Finally, the main system aggregates all the previously defined elements.
system_main = System(
    "System", usage_patterns=[usage_pattern_simple, usage_pattern_advanced, usage_pattern_use_rag,
                                 usage_pattern_fill_rag])

# Now we can generate the JSON file containing all the system's information.
# This JSON serves as a model backup and can be reloaded later in another script or
# in the efootprint interface currently under development.
system_to_json(system_main, False, "system_to_json.json")
