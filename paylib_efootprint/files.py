import os


def create_folder(path):
    if os.environ.get("DJANGO_PROD") != "True" and not os.path.isdir(path):
        os.mkdir(path)
    return path


ROOT = os.path.dirname(os.path.abspath(__file__))
GRAPHS_PATH = os.path.join(ROOT, "graphs")
