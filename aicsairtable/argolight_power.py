import datetime as dt
import math
import os
import warnings

from aics_airtable_core import (
    upload_pandas_dataframe,
)
from dotenv import load_dotenv
import pandas as pd
import scipy.stats

warnings.filterwarnings("ignore")


class ArgoPowerMetrics:
    def __init__(self, file_path: str):
        self.file_path = file_path

        # Establish Headers
        self.dashboard = pd.read_excel(
            os.path.realpath(
                os.path.join(
                    os.path.dirname(__file__),
                    ".",
                    "data",
                    "LaserPower_dashboard_headers.xlsx",
                )
            )
        )
        self.experimental = pd.read_excel(
            os.path.realpath(
                os.path.join(
                    os.path.dirname(__file__),
                    ".",
                    "data",
                    "LaserPower_experimental_headers.xlsx",
                )
            )
        )
        self.linearity = pd.read_excel(
            os.path.realpath(
                os.path.join(
                    os.path.dirname(__file__),
                    ".",
                    "data",
                    "LaserPower_linearity_headers.xlsx",
                )
            )
        )
        # get data
        self.metadata = ArgoPowerMetrics.build_metadata(self.file_path)
        self.datasheet = ArgoPowerMetrics.build_datasheet(self.file_path)

        # Organize data
        self.linearity = ArgoPowerMetrics.build_laser_linearity(
            self.linearity, self.metadata, self.datasheet
        )
        self.experimental = ArgoPowerMetrics.build_laser_experimental(
            self.experimental, self.metadata, self.datasheet
        )
        self.dashboard = ArgoPowerMetrics.build_laser_dashboard(
            self.dashboard, self.linearity, self.experimental
        )

    @staticmethod
    def build_metadata(file_path: str):
        file_name_metadata = file_path.split("/")[-1].upper().split("_")
        metadata = []
        metadata.append(file_name_metadata[0])
        year = int(file_name_metadata[5])
        month = int(file_name_metadata[6])
        day = int(file_name_metadata[7][0:2])
        metadata.append(str(dt.datetime(year, month, day)))
        metadata = metadata + file_name_metadata[1:4]
        return metadata

    @staticmethod
    def build_datasheet(file_path: str):
        datasheet = pd.read_csv(file_path, sep="delimiter")
        datasheet = datasheet["Analysis name"].str.split(";", expand=True)
        datasheet = datasheet[17:]
        datasheet.columns = datasheet.iloc[0]
        datasheet = datasheet[1:]
        datasheet = datasheet.reset_index(drop=True)
        datasheet = datasheet[
            datasheet.columns.drop(list(datasheet.filter(regex="error")))
        ]
        return datasheet

    @staticmethod
    def build_laser_experimental(experimental, metadata, datasheet):

        experimental_raw = datasheet[
            11 : datasheet[
                datasheet.isin(
                    [
                        "measured_optical_power_error",
                        "measured_optical_power_average",
                        "time",
                    ]
                ).any(axis=1)
            ].index[0]
        ]  # this line can be done better
        experimental_raw = experimental_raw.fillna(0).astype(float)
        experimental_raw.set_index("power_instruction", inplace=True)

        for _, row in experimental_raw.iterrows():  # iterate over rows
            for columnIndex, value in row.items():
                if value != 0 and not (math.isnan(value)):
                    power_data = (
                        metadata
                        + [int(columnIndex[:-6])]
                        + experimental_raw[
                            experimental_raw[columnIndex] == value
                        ].index.tolist()
                        + [value]
                    )
                    power_data = pd.Series(power_data, index=experimental.columns)
                    experimental = experimental.append(power_data, ignore_index=True)
        return experimental

    @staticmethod
    def build_laser_linearity(linearity, metadata, datasheet):
        percent_data = datasheet[0:11]
        percent_data = percent_data.fillna(0).astype(float)
        percent_data.set_index("power_instruction", inplace=True)
        for _, row in percent_data.iterrows():  # iterate over rows
            for columnIndex, value in row.items():
                if value != 0 and not (math.isnan(value)):
                    power_data = (
                        metadata
                        + [int(columnIndex[:-6])]
                        + percent_data[
                            percent_data[columnIndex] == value
                        ].index.tolist()
                        + [value]
                    )
                    power_data = pd.Series(power_data, index=linearity.columns)
                    linearity = linearity.append(power_data, ignore_index=True)
        return linearity

    @staticmethod
    def build_laser_dashboard(dashboard, linearity, experimental):
        linearity["System"] = linearity["System"].astype("category")
        linearity["Wavelength (nm)"] = linearity["Wavelength (nm)"].astype("category")
        systems = linearity["System"].cat.categories
        for system in systems:
            pd_sys = linearity[linearity["System"] == system]
            Wavelengths = pd_sys["Wavelength (nm)"].cat.categories
            for wavelength in Wavelengths:
                pd_wavelength = pd_sys[pd_sys["Wavelength (nm)"] == wavelength]
                if not pd_wavelength.empty:
                    pd_current = pd_wavelength[
                        pd_wavelength["Date"] == pd_wavelength["Date"].max()
                    ]
                    row_data = []
                    row_data.append(system)
                    row_data.append(pd_current["Date"].max())  # Max Date
                    row_data.append(wavelength)
                    row_data.append(
                        pd_current["Power (uW)"].max()
                    )  # power in MW of 100% at current date

                    experimental_single_system = experimental[
                        experimental["System"] == system
                    ]
                    experimental_single_system = experimental_single_system[
                        experimental_single_system["Wavelength (nm)"] == wavelength
                    ]
                    experimental_single_system = experimental_single_system[
                        experimental_single_system["Date"] == pd_current["Date"].max()
                    ]
                    row_data.append(
                        experimental_single_system["Power Instruction (%)"].min()
                    )  # Threshold

                    row_data.append(
                        scipy.stats.linregress(
                            x=pd_current["Power Instruction (%)"],
                            y=pd_current["Power (uW)"],
                        ).rvalue
                        ** 2
                    )  # R^2 of current date
                    row_data.append(True)  # modify later with condition
                    if pd_current["Date"].max() == pd_wavelength["Date"].max():
                        row_data.append(True)
                    else:
                        row_data.append(False)
                    row_data = pd.Series(row_data, index=dashboard.columns)
                    dashboard = dashboard.append(row_data, ignore_index=True)
        return dashboard

    def upload(self, env_vars: str):
        try:
            load_dotenv(env_vars)

        except Exception as e:
            raise EnvironmentError(
                "The specified env_var is invalid and failed with " + str(e)
            )

        # Check that all variables from .env are  present
        if (
            any(
                [
                    os.getenv("AIRTABLE_API_KEY"),
                    os.getenv("ARGOLIGHT_POWER_MONTHLY_BASE_KEY"),
                    os.getenv("LASERPOWER_DASHBOARD_TABLE"),
                    os.getenv("LASERPOWER_LINEARITY_TABLE"),
                    os.getenv("LASERPOWER_EXPERIMENTAL_TABLE"),
                ]
            )
            == "None"
        ):
            raise EnvironmentError(
                "Environment variables were not loaded correctly. Some values may be missing."
            )
        upload_pandas_dataframe(
            pandas_dataframe=self.linearity,
            table=os.getenv("LASERPOWER_LINEARITY_TABLE"),
            api_key=os.getenv("AIRTABLE_API_KEY"),
            base_id=os.getenv("ARGOLIGHT_POWER_MONTHLY_BASE_KEY"),
        )
        upload_pandas_dataframe(
            pandas_dataframe=self.experimental,
            table=os.getenv("LASERPOWER_EXPERIMENTAL_TABLE"),
            api_key=os.getenv("AIRTABLE_API_KEY"),
            base_id=os.getenv("ARGOLIGHT_POWER_MONTHLY_BASE_KEY"),
        )
        upload_pandas_dataframe(
            pandas_dataframe=self.dashboard,
            table=os.getenv("LASERPOWER_DASHBOARD_TABLE"),
            api_key=os.getenv("AIRTABLE_API_KEY"),
            base_id=os.getenv("ARGOLIGHT_POWER_MONTHLY_BASE_KEY"),
        )

        # add update to most recent records
