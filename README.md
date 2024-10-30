# e-footprint modelings

This repository is a collection of e-footprint use cases.

All these modelings are powered by the e-footprint library, an open-source project supported by Publicis Sapient and Boavizta.
e-footprint is a Python library that allows to calculate the carbon footprint of different digital services.

fore more details :
- e-footprint github link : https://github.com/Boavizta/e-footprint
- Boavizta link : https://boavizta.org

## Requirements
- Python 3.x
- pip

### Setup
1. Clone the repository : https://github.com/publicissapient-france/e-footprint-modelings

2. Go to sub repository regarding the use case you want to test.
- Modeling of the impact of large language models : See llm_modelings 
- Modeling of the impact of a mobile payment service (Paylib) : See paylib_efootprint.


for example :
```bash
cd llm_modelings
```

3. Create a virtual environment if needed or activate the existing one:
```bash
python -m venv YourNewEnv
source YourNewEnv/bin/activate
```
### OR
```bash
source YourEnv/bin/activate
```

Additionnal information can be found in the README.md of each sub repository.