from aics_airtable_core import (
    airtable_download,
    airtable_upload,
    convert_to_dataframe,
    upload_pandas_dataframe,
)
from argolight_power import ArgoPowerMetrics

"""Top-level package for aicsairtable."""

__author__ = "AICS Software"
__email__ = "AICS_SW@alleninstitute"
# Do not edit this string manually, always use bumpversion
# Details in CONTRIBUTING.md
__version__ = "0.0.0"


def get_module_version():
    return __version__
