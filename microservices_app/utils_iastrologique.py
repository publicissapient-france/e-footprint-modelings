from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pint
from matplotlib import pyplot as plt

from efootprint.builders.hardware.servers_defaults import default_autoscaling
from efootprint.core.usage.job import Job
from efootprint.abstract_modeling_classes.explainable_objects import ExplainableQuantity, EmptyExplainableObject
from efootprint.abstract_modeling_classes.source_objects import SourceValue, Sources, SourceHourlyValues
from efootprint.constants.units import u
from efootprint.utils.plot_emission_diffs import EmissionPlotter


def create_hourly_usage_from_frequency(
        input_volume: float, duration: pint.Quantity, frequency: str, active_days: list = None,
        launch_hours: list = None, start_date: datetime = datetime.strptime("2025-01-01", "%Y-%m-%d"),
        pint_unit: pint.Unit = u.dimensionless):
    """
    Create hourly usage from a volume to distribute among hours with a specific frequency.

    Parameters
    ----------
    input_volume : float The volume to distribute among hours.
    duration : pint.Quantity The duration of the usage.
    frequency : str The frequency of the usage. Must be one of 'daily', 'weekly', 'monthly', or 'yearly'.
    active_days : list, optional The days of the week or month to distribute the volume. Default is None.
    launch_hours : list, optional The hours of the day to distribute the volume. Default is None.
    start_date : datetime, optional The start date of the usage. Default is datetime.strptime("2025-01-01", "%Y-%m-%d").
    pint_unit : pint.Unit, optional The unit of the volume. Default is u.dimensionless.

    Returns
    -------
    SourceHourlyValues The hourly usage.

    """
    if frequency not in ['daily', 'weekly', 'monthly', 'yearly']:
        raise ValueError(f"frequency must be one of 'daily', 'weekly', 'monthly', or 'yearly', got {frequency}.")

    if frequency == 'daily' and active_days is not None:
        raise ValueError(f"active_days must be None for daily frequency, got {active_days}.")

    end_date = start_date + timedelta(days=duration.to(u.day).magnitude)

    if active_days is None:
        if frequency == "weekly":
            active_days = [0]  # default to midnight or Monday
        else:
            active_days = [1]  # default to first day of month or first day of year

    if launch_hours is None:
        launch_hours = [0]  # default to midnight

    period_index = pd.period_range(start=start_date, end=end_date, freq='h')
    values = np.full(shape=len(period_index), fill_value=0)

    for i, period in enumerate(period_index):
        hour_of_day = period.hour  # Hour of the day, 0 to 23
        day_of_week = period.day_of_week  # Day of the week, 0 to 6
        day_of_month = period.day  # Day of the month, 1 to 31
        day_of_year = period.day_of_year  # Day of the year, 1 to 365/366
        if frequency == 'daily':
            if hour_of_day in launch_hours:
                values[i] = input_volume
        elif frequency == 'weekly':
            if day_of_week in active_days and hour_of_day in launch_hours:
                values[i] = input_volume
        elif frequency == 'monthly':
            if day_of_month in active_days and hour_of_day in launch_hours:
                values[i] = input_volume
        elif frequency == 'yearly':
            if day_of_year in active_days and hour_of_day in launch_hours:
                values[i] = input_volume

    df = pd.DataFrame(values, index=period_index, columns=['value'], dtype=f"pint[{str(pint_unit)}]")

    return SourceHourlyValues(df, label="Hourly usage from frequency")


def create_user_volume_for_usage_pattern(
        yearly_usage_series: pd.Series, frequency: str, active_days: list = None, launch_hours: list = None):

    """
    Create hourly usage from a pandas Series of yearly usage to distribute among hours with a specific frequency.

    Parameters
    ----------
    yearly_usage_series : pd.Series The yearly usage to distribute among hours.
    frequency : str The frequency of the usage. Must be one of 'daily', 'weekly', 'monthly', or 'yearly'.
    active_days : list, optional The days of the week or month to distribute the volume. Default is None.
    launch_hours : list, optional The hours of the day to distribute the volume. Default is None.

    Returns
    -------
    SourceHourlyValues The hourly usage.
    """

    yearly_visits_as_hourly_quantities = []

    for i in range(len(yearly_usage_series)):
        year = yearly_usage_series.index[i]
        nb_visits_that_year = yearly_usage_series.iloc[i]

        if frequency == "daily":
            nb_active_days_per_year = 365
        elif frequency == "weekly":
            nb_active_days_per_year = 52 * len(active_days)
        elif frequency == "monthly":
            nb_active_days_per_year = 12 * len(active_days)
        elif frequency == "yearly":
            nb_active_days_per_year = len(active_days)

        nb_hourly_visits = nb_visits_that_year / (nb_active_days_per_year * len(launch_hours))

        start_date = datetime(year, 1, 1)
        duration = (datetime(year + 1, 1, 1) - start_date).days * u.day - 1 * u.hour
        yearly_usage = create_hourly_usage_from_frequency(
            nb_hourly_visits, duration, frequency, active_days, launch_hours, start_date)

        yearly_visits_as_hourly_quantities.append(yearly_usage)

    visits_over_all_years = sum(yearly_visits_as_hourly_quantities, start=EmptyExplainableObject())
    visits_over_all_years.left_parent = None
    visits_over_all_years.right_parent = None
    visits_over_all_years.label = "User volume for usage pattern"

    return visits_over_all_years


#hypothesis definition
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
def create_server(name, instance_type, serv_storage):
    server_conf =hp_instance_configuration[instance_type]
    return default_autoscaling(name, **server_conf, storage=serv_storage)

def create_job(name, data_upload, data_download, data_stored, request_duration, ram_needed, cpu_needed, server,
        nb_result_step_trial=None):
    data_upload = SourceValue(data_upload, Sources.HYPOTHESIS, label=f"Data upload for {name} job")
    data_download = SourceValue(data_download, Sources.HYPOTHESIS, label=f"Data download for {name} job")
    data_stored = SourceValue(data_stored, Sources.HYPOTHESIS, label=f"Data stored for {name} job")
    request_duration = SourceValue(request_duration, Sources.HYPOTHESIS, label=f"Request duration for {name} job")
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
        ram_needed=SourceValue(ram_needed, Sources.HYPOTHESIS, label=f"RAM needed for {name} job"),
        cpu_needed=SourceValue(cpu_needed, Sources.HYPOTHESIS, label=f"CPU needed for {name} job"),
        server=server
    )


def plot_from_system(emissions_dict__old, emissions_dict__new, title, filepath, figsize):
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize)

    EmissionPlotter(
        ax, emissions_dict__old, emissions_dict__new, title=title, rounding_value=1,
        timespan=ExplainableQuantity(1 * u.year, "one year")).plot_emission_diffs()
    plt.savefig(filepath)

