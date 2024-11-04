# Description
This project models various user journeys and their impact on system resources for a specific use case: the usage of Gen AI tools within an internal information system. It uses Python and specific libraries to define user journey steps, usage patterns, and resource requirements. The code allows for result analysis and visualizes the impacts in terms of CO2 emissions.

This project relies heavily on the `e-footprint` library, an open-source project supported by Publicis Sapient and Boavizta. `e-footprint` is a Python library that calculates the carbon footprint of different digital services.

More details:
- e-footprint GitHub link: https://github.com/Boavizta/e-footprint
- Boavizta link: https://boavizta.org

# Prerequisites
- Python 3.x
- pip

# Installation
1. Clone the repository:
```bash
git clone https://github.com/morzu117/system-sg-modelling.git
cd system-sg-modelling
```

(Optional) Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

# Usage
1. Modify the parameters in `main.py` as needed.
2. Run the main script:
```bash
python main.py
```
3. To view the results, open the Jupyter notebook `modelisation.ipynb`:
```bash
jupyter notebook
```

# Project Structure
- `main.py`: Contains the main logic for defining user journeys and usage models.
- `README.md`: This file, describing the project and how to use it.
- `builder`: Contains classes for building usage models and user journeys.
- `requirements.txt`: Python dependencies file.
- `modelisation.ipynb`: Jupyter notebook for visualizing results.

# Modeled User Journeys
- **Chat with a simple bot**: `user_journey_chat_with_simple_bot`
- **Chat with an advanced bot**: `user_journey_chat_with_advanced_bot`
- **Using RAG**: `user_journey_use_rag`
- **Filling RAG**: `user_journey_fill_rag`