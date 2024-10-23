from use_cases.multiservice_app_carbon_case.iastrologique_usage import iastrologique_yearly_modeling, PLOTS_PATH
from footprint_model.utils.graph_representation import (
    build_graph, SERVICES_VIEW_CLASSES_TO_IGNORE, USAGE_PATTERN_VIEW_CLASSES_TO_IGNORE,
    SERVICES_AND_INFRA_VIEW_CLASSES_TO_IGNORE, save_graph_as_both_html_and_png)
from footprint_model.utils.calculus_representation import build_graph as build_calculus_graph

import os

POPULATION_VIEW_CLASSES_TO_IGNORE = [
    "System", "UserJourney", "UserJourneyStep", "TimeIntervals", "Network", "Service", "Hardware", "Server", "Storage"]

if __name__ == "__main__":
    iastrologique_system = iastrologique_yearly_modeling(20000, 200000)

    G = build_graph(iastrologique_system.usage_patterns[0], classes_to_ignore=SERVICES_VIEW_CLASSES_TO_IGNORE)
    save_graph_as_both_html_and_png(G, os.path.join(PLOTS_PATH, "services_view.html"))

    G = build_graph(iastrologique_system, classes_to_ignore=USAGE_PATTERN_VIEW_CLASSES_TO_IGNORE)
    save_graph_as_both_html_and_png(G, os.path.join(PLOTS_PATH, "usage_pattern_view.html"))

    G = build_graph(iastrologique_system, classes_to_ignore=SERVICES_AND_INFRA_VIEW_CLASSES_TO_IGNORE)
    save_graph_as_both_html_and_png(G, os.path.join(PLOTS_PATH, "services_and_infra_view.html"))

    G = build_graph(iastrologique_system, classes_to_ignore=POPULATION_VIEW_CLASSES_TO_IGNORE)
    save_graph_as_both_html_and_png(G, os.path.join(PLOTS_PATH, "population_view.html"))

    G = build_calculus_graph(iastrologique_system.energy_footprints()["Servers"], label_len_threshold=0)
    save_graph_as_both_html_and_png(G, os.path.join(PLOTS_PATH, "calculus_output.html"))
