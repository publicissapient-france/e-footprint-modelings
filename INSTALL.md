# Install

## Clone the repository

```bash
git clone git@github.com:publicissapient-france/e-footprint-modelings.git
cd e-footprint-modelings
```

## Go to the modeling repository you want to work on (e.g. llm_modelings)

```bash
cd llm_modelings
```

## Install the requirements

Each package has its own requirements file. You can install the requirements by running the following commands.
Here is an example using conda as an env manager (but you could use other env manager as pyvenv or
virtualenvwrapper):

```bash
conda create -n e-footprint python=3.11.2
conda activate e-footprint
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Optionally, if you want to use jupyter notebooks during the development process:

```
conda install ipykernel jupyter
python -m ipykernel install --user --name=e-footprint
```

If you have trouble managing the python versions on your laptop you can check out [pyenv](https://github.com/pyenv/pyenv) and also manage your virtual environments with [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)
