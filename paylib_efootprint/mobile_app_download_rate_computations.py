from efootprint.abstract_modeling_classes.explainable_object_base_class import Source
from efootprint.abstract_modeling_classes.source_objects import SourceValue
from efootprint.constants.sources import Sources
from efootprint.constants.units import u


source_hibernation_android = Source(
    "developper.android.com and Numerama",
    link="https://www.numerama.com/tech/132165-les-versions-dandroid-les-plus-utilisees.html and https://developer.android.com/topic/performance/app-hibernation?hl=fr")
percentage_hibernation_android = SourceValue(
    0.5 * u.dimensionless, source_hibernation_android, "Percentage of Android phones with app hibernation functionality"
)
source_hibernation_iphone = Source(
    "macreports and Statista",
    link="https://macreports.com/why-some-apps-are-disappearing-how-to-disable-offload-unused-apps and https://www.statista.com/statistics/565270/apple-devices-ios-version-share-worldwide/")
percentage_hibernation_iphone = SourceValue(
    1 * u.dimensionless, source_hibernation_iphone, "Percentage of iPhones with app hibernation functionality")

android_fraction_of_users_active_over_3_months = SourceValue(
    0.2 * u.dimensionless, label="Fraction of Android users active on Paylib over 3 months")

iphone_fraction_of_users_active_over_3_months = SourceValue(
    0.2 * u.dimensionless, label="Fraction of iPhone users active on Paylib over 3 months")

hundred_percent = SourceValue(1 * u.dimensionless, Sources.USER_DATA, "100 %")


android_paylib_app_update_rate = SourceValue(
    4 * u.user_journey / (u.user * u.year), Sources.USER_DATA, "Android app release rate")
iphone_paylib_app_update_rate = SourceValue(
    6 * u.user_journey / (u.user * u.year), Sources.USER_DATA, "iPhone app release rate")

download_rate_for_user_with_hibernating_app = SourceValue(
    1 * u.user_journey / (u.user * u.year), Sources.HYPOTHESIS, "Download rate for user with hibernating app")

android_fraction_of_inactive_users = hundred_percent - android_fraction_of_users_active_over_3_months
average_paylib_app_download_rate_android = (
    (android_fraction_of_users_active_over_3_months
     + (hundred_percent - percentage_hibernation_android) * android_fraction_of_inactive_users)
    * android_paylib_app_update_rate +
    android_fraction_of_inactive_users * percentage_hibernation_android * download_rate_for_user_with_hibernating_app)

iphone_fraction_of_inactive_users = hundred_percent - iphone_fraction_of_users_active_over_3_months
average_paylib_app_download_rate_iphone = (
    (iphone_fraction_of_users_active_over_3_months
     + (hundred_percent - percentage_hibernation_iphone) * iphone_fraction_of_inactive_users)
    * iphone_paylib_app_update_rate +
    iphone_fraction_of_inactive_users * percentage_hibernation_iphone * download_rate_for_user_with_hibernating_app)