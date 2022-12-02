from datetime import datetime
import os
import time

from watchdog.utils.dirsnapshot import (
    DirectorySnapshot,
    DirectorySnapshotDiff,
)

from ..argolight_power import ArgoPowerMetrics

LOG_PATH = "ArgoPowerMonthlyLog"

WATCH_PATH = (
    "/allen/aics/microscopy/PRODUCTION/OpticalControl/ArgoLight/ArgoPower_Monthly"
)
ENV_VARS = "/allen/aics/microscopy/brian_whitney/repos/aicsairtable/.env"


# monitor class
class ArgoPowerMonthlyMonitor:
    def __init__(self):
        self._path = None
        self._is_recursive = True
        self._oldSnapshot = None
        self._newSnapshot = None
        self._diffSnapshot = None
        self._is_started = False

        # .env stuff

    def watch(self, path, recursive=True):
        self._path = os.path.abspath(path)
        self._is_recursive = recursive

    def scan(self):
        if not self._is_started:
            self._is_started = True
            self._newSnapshot = DirectorySnapshot(
                path=self._path,
                recursive=self._is_recursive,
            )
            self._oldSnapshot = self._newSnapshot
        else:
            self._newSnapshot = DirectorySnapshot(
                path=self._path,
                recursive=self._is_recursive,
            )
            self._diffSnapshot = DirectorySnapshotDiff(
                self._oldSnapshot, self._newSnapshot
            )
            self._oldSnapshot = self._newSnapshot
            self.process_diff()
        return

    def process_diff(self):
        for path in self._diffSnapshot.files_created:
            if ".csv" in path:
                print(path)
            try:
                ArgoPower = ArgoPowerMetrics(path, ENV_VARS)
                ArgoPower.upload()
            except Exception as e:
                print(str(e))
                pass

    def removeFile(self, fileName):
        try:
            os.remove(fileName)
        except Exception:
            self.writeLog("Unexpected removeFile error for file " + fileName)
            return

    def writeLog(self, message):
        with open(LOG_PATH, "a+") as f:
            i = datetime.now()
            f.write(i.strftime("%Y/%m/%d %H:%M:%S") + " " + message + "\n")


if __name__ == "__main__":

    myMonitor = ArgoPowerMonthlyMonitor()
    myMonitor.watch(path=WATCH_PATH, recursive=True)
    myMonitor.scan()

    while True:
        myMonitor.scan()
        time.sleep(10)  # Check every 5 min
