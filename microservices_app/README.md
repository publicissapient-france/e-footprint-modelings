# e-footprint : IAstrologique modelisation

This repository is a modelisation of different user journeys and their impacts on system resources for a particular use case, the use of Gen AI tools.

All these modelings are powered by the e-footprint library, an open-source project supported by Publicis Sapient and Boavizta.
e-footprint is a Python library that allows to calculate the carbon footprint of different digital services.

fore more details :
- e-footprint guthub link : https://github.com/Boavizta/e-footprint
- Boavizta link : https://boavizta.org

## Requirements
- Python 3.x
- pip

### Setup
1. Virtual environment :
```bash
Create a virtual environment if needed or activate the existing one:
```bash
python -m venv YourNewEnv
source YourNewEnv/bin/activate
```
### OR
```bash
source YourEnv/bin/activate
```

2. Install dependencies :
```bash
pip install -r requirements.txt
```

## Project structure
- `iastrologique_usage.py` : Contains the main logic to define user journeys and usage models.
- `README.md` : This file, describing the project and how to use it.
- `utils_iastrologique.py` : Contains methods to facilitate the build of some e-footprint objects
- `requirements.txt` : Python dependencies file.
- `iastrologique_modelisation.ipynb` : Jupyter notebook to visualize the results.