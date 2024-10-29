import os
import sys
import pandas as pd
import pint
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from efootprint.builders.hardware.servers_defaults import default_autoscaling
from efootprint.core.usage.job import Job

sys.path.append(os.path.join("..", ".."))
from efootprint.abstract_modeling_classes.explainable_objects import ExplainableQuantity
from efootprint.abstract_modeling_classes.source_objects import SourceValue, Sources, SourceHourlyValues
from efootprint.core.hardware.servers.autoscaling import Autoscaling
from efootprint.constants.units import u

from efootprint.utils.plot_emission_diffs import EmissionPlotter

from matplotlib import pyplot as plt



# Create sub_hourly usage from a list of hours and a volume to distribute among them with a specific frequency
def create_hourly_usage_from_frequency(
        input_volume: float, start_date: datetime, pint_unit: pint.Unit, type_frequency: str,
        duration, only_work_days: bool, time_list:list = None, launch_hour_list: list = None):

    if start_date is None:
        start_date = datetime.strptime("2025-01-01", "%Y-%m-%d")
    if pint_unit is None:
        pint_unit = pint.Unit(u.dimensionless)
    if type_frequency not in ['daily', 'weekly', 'monthly', 'yearly']:
        raise ValueError("type_frequency must be one of 'daily', 'weekly', 'monthly', or 'yearly'.")

    if isinstance(duration, pint.Quantity):
        if duration.units == u.day:
            end_date = start_date + timedelta(days=duration.magnitude - 1)
        elif duration.units == u.week:
            end_date = start_date + timedelta(weeks=duration.magnitude) - timedelta(days=1)
        elif duration.units == u.month:
            end_date = start_date + relativedelta(months=duration.magnitude) - timedelta(days=1)
        elif duration.units == u.year:
            end_date = start_date + relativedelta(years=duration.magnitude) - timedelta(days=1)
        else:
            raise ValueError("Unsupported unit for duration. Use days, weeks, months, or years.")
        end_date = end_date.replace(hour=23)
    else:
        raise TypeError("duration must be a pint.Quantity with time units like days, weeks, months, or years (e.g., 2*u.month).")

    if time_list is None:
        if type_frequency == 'daily':
            time_list = [0]  # default to midnight
        elif type_frequency == 'weekly':
            time_list = [1]  # default to Monday
        elif type_frequency == 'monthly':
            time_list = [1]  # default to the first day of the month
        elif type_frequency == 'yearly':
            time_list = [1]  # default to the first day of the year
        if launch_hour_list is None:
            launch_hour_list = [0]  # default to midnight

    period_index = pd.period_range(start=start_date, end=end_date, freq='h')
    df = pd.DataFrame(0, index=period_index, columns=['value'], dtype=f"pint[{str(pint_unit)}]")

    for current_hour in df.index:
        hour_of_day = current_hour.hour
        day_of_week = current_hour.to_timestamp().weekday()
        day_of_month = current_hour.day
        day_of_year = current_hour.to_timestamp().timetuple().tm_yday  # Day of the year, 1 to 365/366
        if type_frequency == 'daily':
            if hour_of_day in time_list and (not only_work_days or day_of_week < 5):
                df.at[current_hour, 'value'] = input_volume
        elif type_frequency == 'weekly':
            if day_of_week in time_list and hour_of_day in launch_hour_list:
                df.at[current_hour, 'value'] = input_volume
        elif type_frequency == 'monthly':
            if day_of_month in time_list and hour_of_day in launch_hour_list:
                df.at[current_hour, 'value'] = input_volume
        elif type_frequency == 'yearly':
            if day_of_year in time_list and hour_of_day in launch_hour_list:
                df.at[current_hour, 'value'] = input_volume

    return SourceHourlyValues(df, label="Hourly usage")

def  create_user_volume_for_usage_pattern(type_frequency: str, only_work_days: bool, time_list:list = None,
                                          launch_hour_list: list = None, use_coefficient: bool = False):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_directory, 'yearly_nb_of_users.csv')
    yearly_usage_df = pd.read_csv(csv_file_path)

    list_exp_hourly_quantity = []

    for i in range(len(yearly_usage_df)):
        year = yearly_usage_df["year"].iloc[i]
        nb_paid_users_that_year = yearly_usage_df["nb_paid_users"].iloc[i]
        nb_free_users_that_year = yearly_usage_df["nb_free_users"].iloc[i]

        start_date = datetime(year, 1, 1)
        if year % 4 == 0:
            duration = 366 * u.day
        else:
            duration = 365 * u.day

        if only_work_days:
            working_days =(sum(1 for day in range(duration.magnitude)
                               if (datetime(year, 1, 1)
                                   + timedelta(days=day)).weekday() < 5)) * u.day
        else:
            working_days = 0 * u.day

        duration_split = duration - working_days

        if use_coefficient:
            coef_nb_paid_users = yearly_usage_df["coef_nb_paid_users"].iloc[i]
            coef_nb_free_users = yearly_usage_df["coef_nb_free_users"].iloc[i]
            nb_hourly_users = (nb_paid_users_that_year * coef_nb_paid_users + nb_free_users_that_year * coef_nb_free_users)
        else:
            nb_hourly_users = nb_paid_users_that_year + nb_free_users_that_year

        if type_frequency == 'daily':
            nb_hourly_users = round((nb_hourly_users/duration_split.magnitude)/ len(time_list), 0)
        elif type_frequency == 'weekly' or type_frequency == 'monthly':
            nb_hourly_users = round((nb_hourly_users/duration_split.magnitude)/ len(time_list) / len(launch_hour_list), 0)

        yearly_usage = create_hourly_usage_from_frequency(
            nb_hourly_users, start_date, pint.Unit(u.dimensionless), "daily", duration,
           only_work_days, time_list, launch_hour_list)

        list_exp_hourly_quantity.append(yearly_usage)

    return_object = None

    for i in range(len(list_exp_hourly_quantity)):
        if i == 0:
            return_object = list_exp_hourly_quantity[i]
        else:
            return_object += list_exp_hourly_quantity[i]

    return return_object


#hypothesis definition
#---------------------------------------------------------------------------
#STORAGE
#---------------------------------------------------------------------------
#The default capacity of a SSD is set to 1TB
#---------------------------------------------------------------------------
#SERVER
#---------------------------------------------------------------------------
#Definition of two instance configurations, one for large instances and one for small instances (for storage specifically)
#Use of an instance type variable to define easily the instance type
hp_instance_configuration = {
    "lg": {
        "carbon_footprint_fabrication": SourceValue(1000 * u.kg, Sources.HYPOTHESIS),
        "power": SourceValue(300 * u.W, Sources.HYPOTHESIS),
        "idle_power": SourceValue(50 * u.W, Sources.HYPOTHESIS),
        "ram": SourceValue(256 * u.GB, Sources.USER_DATA),
        "cpu_cores": SourceValue(64 * u.core, Sources.USER_DATA)
    },
    "sm": {
        "carbon_footprint_fabrication": SourceValue(200 * u.kg, Sources.HYPOTHESIS),
        "power": SourceValue(150 * u.W, Sources.HYPOTHESIS),
        "idle_power": SourceValue(20 * u.W, Sources.HYPOTHESIS),
        "ram": SourceValue(32 * u.GB, Sources.USER_DATA),
        "cpu_cores": SourceValue(8 * u.core, Sources.USER_DATA)
    }
}
#---------------------------------------------------------------------------
#JOB
#---------------------------------------------------------------------------
hp_job_type={
    "default": {
        "data_upload": SourceValue(10 * u.kB, Sources.HYPOTHESIS),
        "data_download": SourceValue(500 * u.kB, Sources.HYPOTHESIS),
        "data_stored": SourceValue(0 * u.kB, Sources.HYPOTHESIS),
        "request_duration": SourceValue(1 * u.s, Sources.HYPOTHESIS),
        "server_ram_needed": SourceValue(1*u.GB, Sources.HYPOTHESIS),
        "cpu_needed": SourceValue(1*u.core, Sources.HYPOTHESIS)
    },
    "base_calcul_a": {
        "data_upload": SourceValue(10 * u.kB, Sources.HYPOTHESIS),
        "data_download": SourceValue(2 * u.MB, Sources.HYPOTHESIS),
        "data_stored": SourceValue(0 * u.kB, Sources.HYPOTHESIS),
        "request_duration": SourceValue(3 * u.s, Sources.HYPOTHESIS),
        "server_ram_needed": SourceValue(2*u.GB, Sources.HYPOTHESIS),
        "cpu_needed": SourceValue(2*u.core, Sources.HYPOTHESIS)
    },
    "base_calcul_b": {
        "data_upload": SourceValue(0 * u.kB, Sources.HYPOTHESIS),
        "data_download": SourceValue(500 * u.MB, Sources.HYPOTHESIS),
        "data_stored": SourceValue(0 * u.kB, Sources.HYPOTHESIS),
        "request_duration": SourceValue(1 * u.s, Sources.HYPOTHESIS),
        "server_ram_needed": SourceValue(2*u.GB, Sources.HYPOTHESIS),
        "cpu_needed": SourceValue(2*u.core, Sources.HYPOTHESIS)
    },
    "jenkins": {
        "data_upload": SourceValue(100 * u.kB, Sources.HYPOTHESIS),
        "data_download": SourceValue(100 * u.kB, Sources.HYPOTHESIS),
        "data_stored": SourceValue(0 * u.kB, Sources.HYPOTHESIS),
        "request_duration": SourceValue(1 * u.s, Sources.HYPOTHESIS),
        "server_ram_needed": SourceValue(1*u.GB, Sources.HYPOTHESIS),
        "cpu_needed": SourceValue(1*u.core, Sources.HYPOTHESIS)
    }
}

def create_server(name, instance_type, serv_storage):
    server_conf =hp_instance_configuration[instance_type]
    return default_autoscaling(name, **server_conf, storage=serv_storage)


def create_server_save(name, instance_type, serv_storage):
    return Autoscaling(
        name,
        carbon_footprint_fabrication=hp_instance_configuration[instance_type]["carbon_footprint"],
        power=hp_instance_configuration[instance_type]["power"],
        lifespan=SourceValue(6 * u.year, Sources.HYPOTHESIS),
        idle_power=hp_instance_configuration[instance_type]["idle_power"],
        ram=hp_instance_configuration[instance_type]["ram"],
        cpu_cores=hp_instance_configuration[instance_type]["cpu"],
        power_usage_effectiveness=SourceValue(1.2 * u.dimensionless, Sources.HYPOTHESIS),
        average_carbon_intensity=SourceValue(100 * u.g / u.kWh, Sources.HYPOTHESIS),
        server_utilization_rate=SourceValue(0.5 * u.dimensionless, Sources.HYPOTHESIS),
        base_ram_consumption=SourceValue(0.5 * u.GB, Sources.HYPOTHESIS),
        base_cpu_consumption=SourceValue(0.5 * u.core, Sources.HYPOTHESIS),
        storage=serv_storage
    )

def create_job(name, data_upload, data_download, data_stored, request_duration, ram_needed, cpu_needed, server,
        nb_result_step_trial=None):
    if nb_result_step_trial is not None:
        data_upload = data_upload * nb_result_step_trial
        data_download = data_download * nb_result_step_trial
        data_stored = data_stored * nb_result_step_trial
        request_duration = request_duration * nb_result_step_trial
    else :
        data_upload = SourceValue(data_upload, Sources.HYPOTHESIS)
        data_download = SourceValue(data_download, Sources.HYPOTHESIS)
        data_stored = SourceValue(data_stored, Sources.HYPOTHESIS)
        request_duration = SourceValue(request_duration, Sources.HYPOTHESIS)
    return Job(
        name=name,
        data_upload=data_upload,
        data_download=data_download,
        data_stored=data_stored,
        request_duration=request_duration,
        ram_needed=SourceValue(ram_needed, Sources.HYPOTHESIS),
        cpu_needed=SourceValue(cpu_needed, Sources.HYPOTHESIS),
        server=server
    )

def create_job_with_template_dict(name, job_template, server, nb_result_step_trial=None):
    data_upload = hp_job_type[job_template]["data_upload"]
    data_download = hp_job_type[job_template]["data_download"]
    data_stored = hp_job_type[job_template]["data_stored"]
    request_duration = hp_job_type[job_template]["request_duration"]
    if nb_result_step_trial is not None:
        data_upload = data_upload * nb_result_step_trial
        data_download = data_download * nb_result_step_trial
        data_stored = data_stored * nb_result_step_trial
        request_duration = request_duration * nb_result_step_trial
    return Job(
        name=name,
        data_upload=data_upload,
        data_download=data_download,
        data_stored=data_stored,
        request_duration=request_duration,
        ram_needed=hp_job_type[job_template]["server_ram_needed"],
        cpu_needed=hp_job_type[job_template]["cpu_needed"],
        server=server
    )



def plot_from_system(emissions_dict__old, emissions_dict__new, title, filepath, figsize):
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize)

    EmissionPlotter(
        ax, emissions_dict__old, emissions_dict__new, title=title, rounding_value=1,
        timespan=ExplainableQuantity(1 * u.year, "one year")).plot_emission_diffs()
    plt.savefig(filepath)

