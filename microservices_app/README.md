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
1. Clone the repository :


1bis. Create a virtual environment if needed:
```bash
python -m venv YourNewEnv
source YourNewEnv/bin/activate
```

2. Install dependencies :
```bash
pip install -r requirements.txt
```

## Usage
1. Modify the parameters in `main.py` according to your needs.
2. Run the main script to test the modelisation :
```bash
python iastrologique_usage.py
```

3. To visualize the results, open the Jupyter notebook modelisation.ipynb :
```bash
jupyter notebook
```


## Project structure
- `iastrologique_usage.py` : Contains the main logic to define user journeys and usage models.
- `utils_iastrologique.py` : Contains utility functions to build easily e-footprint objets.
- `requirements.txt` : Python dependencies file.
- `iastrologique_modelisation.ipynb` : Jupyter notebook to visualize the results.