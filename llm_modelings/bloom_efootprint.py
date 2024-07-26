import os.path

from efootprint.abstract_modeling_classes.source_objects import SourceValue, Sources, SourceObject, Source
from efootprint.api_utils.system_to_json import system_to_json
from efootprint.core.usage.user_journey import UserJourney, UserJourneyStep
from efootprint.core.usage.job import Job
from efootprint.core.hardware.servers.autoscaling import Autoscaling
from efootprint.core.hardware.storage import Storage
from efootprint.core.service import Service
from efootprint.core.hardware.device_population import DevicePopulation
from efootprint.builders.hardware.devices_defaults import default_laptop
from efootprint.core.usage.usage_pattern import UsagePattern
from efootprint.core.hardware.network import Network
from efootprint.core.system import System
from efootprint.constants.countries import Countries
from efootprint.constants.units import u


bloom_paper_source = Source("Estimating the Carbon Footprint of BLOOM", "https://arxiv.org/abs/2211.05100")

gpu_hours = SourceValue(1082000 * u.h, bloom_paper_source, "gpu_hours")
gpu_lifetime = SourceValue(6 * u.year, bloom_paper_source, "gpu_lifetime")
total_training_time = SourceValue(119 * u.day, bloom_paper_source, "total_training_time")
gpu_power = SourceValue(400 * u.W, bloom_paper_source, "GPU Power")
gpu_idle_power = SourceValue(50 * u.W, bloom_paper_source, "GPU idle power")

NB_OF_GPUs = (gpu_hours / total_training_time).set_label("Number of Gpus")

carbon_footprint_fabrication_server_without_gpu = SourceValue(
    2500 * u.kg, bloom_paper_source, "Carbon footprint without GPU")
carbon_footprint_fabrication_one_gpu = SourceValue(150 * u.kg, bloom_paper_source, "Carbon footprint one GPU")

cpu_core_per_gpu = SourceValue(1 * u.core, label="1 CPU core / GPU")
cpu_core_per_gpu_uj = SourceValue(1 * u.core / u.uj, label="1 CPU core / GPU / uj")

server = Autoscaling(
    "Training GPU server",
    carbon_footprint_fabrication=(
        carbon_footprint_fabrication_server_without_gpu + NB_OF_GPUs * carbon_footprint_fabrication_one_gpu
        ).set_label("default"),
    power=(gpu_power * NB_OF_GPUs).set_label("default"),
    lifespan=SourceValue(6 * 0.85 * u.year, bloom_paper_source),
    idle_power=(gpu_idle_power * NB_OF_GPUs).set_label("default"),
    ram=SourceValue(128 * u.GB, Sources.HYPOTHESIS),
    cpu_cores=(NB_OF_GPUs * cpu_core_per_gpu).set_label("default"),
    power_usage_effectiveness=SourceValue(1.4 * u.dimensionless, Sources.HYPOTHESIS),
    average_carbon_intensity=SourceValue(57 * u.g / u.kWh, bloom_paper_source),
    server_utilization_rate=SourceValue(1 * u.dimensionless, Sources.USER_DATA)
)

storage = Storage(
    "SSD storage",
    carbon_footprint_fabrication=SourceValue(160 * u.kg, Sources.STORAGE_EMBODIED_CARBON_STUDY),
    power=SourceValue(1.3 * u.W, Sources.STORAGE_EMBODIED_CARBON_STUDY),
    lifespan=SourceValue(6 * u.years, Sources.HYPOTHESIS),
    idle_power=SourceValue(0 * u.W, Sources.HYPOTHESIS),
    storage_capacity=SourceValue(1 * u.TB, Sources.STORAGE_EMBODIED_CARBON_STUDY),
    power_usage_effectiveness=SourceValue(1.2 * u.dimensionless, Sources.HYPOTHESIS),
    average_carbon_intensity=SourceValue(57 * u.g / u.kWh, bloom_paper_source),
    data_replication_factor=SourceValue(3 * u.dimensionless, Sources.HYPOTHESIS),
)

service = Service(
    "Bloom model training", server, storage, base_ram_consumption=SourceValue(0 * u.MB, Sources.HYPOTHESIS),
    base_cpu_consumption=SourceValue(0 * u.core, Sources.HYPOTHESIS))

bloom_training_step = UserJourneyStep(
    "Bloom training", user_time_spent=SourceValue(24 * u.h / u.uj, Sources.USER_DATA),
    jobs=[Job("Bloom training job", service, SourceValue(1 * u.TB / u.uj, Sources.USER_DATA),
              SourceValue(1 * u.TB / u.uj, Sources.USER_DATA),
              request_duration=SourceValue(24 * u.h, Sources.HYPOTHESIS),
              cpu_needed=(NB_OF_GPUs * cpu_core_per_gpu_uj).set_label("default"),
              ram_needed=SourceValue(100 * u.MB / u.uj, Sources.HYPOTHESIS))])

training_uj = UserJourney("Training", uj_steps=[bloom_training_step])

bloom_dev = DevicePopulation("Bloom dev", SourceValue(1 * u.user), Countries.FRANCE(), [default_laptop()])

network = Network("WIFI network", SourceValue(0.05 * u("kWh/GB"), Sources.TRAFICOM_STUDY))


training_up = UsagePattern(
    "Training", training_uj, bloom_dev,
    network, (total_training_time * SourceValue(1 * u.user_journey / (u.user * u.day * u.year))).set_label("default"),
    SourceObject([[0, 23]]))

GPU_INFERENCE_NB = SourceValue(16 * u.dimensionless)

server_inference = Autoscaling(
    "Inference GPU server",
    carbon_footprint_fabrication=(
        carbon_footprint_fabrication_server_without_gpu + GPU_INFERENCE_NB * carbon_footprint_fabrication_one_gpu
        ).set_label("default"),
    power=(GPU_INFERENCE_NB * gpu_power).set_label("default"),
    lifespan=SourceValue(6 * 0.85 * u.year, bloom_paper_source),
    idle_power=(GPU_INFERENCE_NB * gpu_idle_power).set_label("default"),
    ram=SourceValue(128 * u.GB, Sources.HYPOTHESIS),
    cpu_cores=(GPU_INFERENCE_NB * cpu_core_per_gpu).set_label("default"),
    power_usage_effectiveness=SourceValue(1.2 * u.dimensionless, Sources.HYPOTHESIS),
    average_carbon_intensity=SourceValue(57 * u.g / u.kWh, bloom_paper_source),
    server_utilization_rate=SourceValue(1 * u.dimensionless, Sources.USER_DATA)
)

service_inference = Service(
    "Bloom model inference", server_inference, storage, base_ram_consumption=SourceValue(0 * u.MB, Sources.HYPOTHESIS),
    base_cpu_consumption=SourceValue(0 * u.core, Sources.HYPOTHESIS))

request_per_hour = SourceValue(558 / u.hour, bloom_paper_source, "Nb of requests per hour")
average_cluster_power_measured = SourceValue(1664 * u.W, bloom_paper_source, "Average cluster power measured")
average_utilisation_rate = average_cluster_power_measured / server_inference.power
request_duration = average_utilisation_rate / request_per_hour

bloom_inference_step = UserJourneyStep(
    "Bloom inference",
    user_time_spent=(
        request_duration * SourceValue(1 / u.user_journey, label="One request per user session")).set_label("default"),
    jobs=[Job("Bloom inference job", service_inference, SourceValue(100 * u.kB / u.uj, Sources.USER_DATA),
              SourceValue(100 * u.kB / u.uj, Sources.USER_DATA),
              request_duration=request_duration.set_label("default"),
              cpu_needed=(NB_OF_GPUs * cpu_core_per_gpu_uj).set_label("default"),
              ram_needed=SourceValue(100 * u.MB / u.uj, Sources.HYPOTHESIS))])

inference_uj = UserJourney("Inference", uj_steps=[bloom_inference_step])

french_pop = DevicePopulation("Bloom users", SourceValue(1 * u.user), Countries.FRANCE(), [default_laptop()])

inference_up = UsagePattern(
    "Discussions", inference_uj, french_pop,
    network, request_per_hour * SourceValue(1 * u.user_journey / u.user, label="One user journey per user"),
    SourceObject([[0, 23]]))

system = System("Bloom usage in France", [inference_up, training_up])

print(f"Server carbon footprint is {(server.energy_footprint + server.instances_fabrication_footprint).value}")
print(f"Total system carbon footprint is {system.total_footprint.value}")

system.plot_footprints_by_category_and_object()
system.object_relationship_graph_to_file("Bloom object relationship graph.html")

root_dir = os.path.dirname(os.path.abspath(__file__))

system_to_json(system, save_calculated_attributes=False, output_filepath=os.path.join(root_dir, "bloom_modeling.json"))
