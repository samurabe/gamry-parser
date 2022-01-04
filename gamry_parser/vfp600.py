import gamry_parser as parser
import pandas as pd
import re
from io import StringIO


class VFP600(parser.GamryParser):
    """Load experiment data generated by Gamry VFP600 software (expected in EXPLAIN format, including header)"""

    def __init__(self, filename: str = None, to_timestamp: bool = None):
        """VFP600.__init__

        Args:
            filename (str, optional): filepath containing CHRONOA experiment data. Defaults to None
            to_timestamp (bool, optional): this argument is ignored by the VFP600 class.
        Returns:
            None

        """
        # No information about experiment time is available with VFP600 files, so no conversion of samples to pd.Timestamp is possible.
        super().__init__(filename=filename, to_timestamp=False)

    def load(self, filename: str = None):
        """save experiment information to \"header\", then save curve data to \"curves\"

        Args:
            filename (str, optional): file containing VFP600 data. defaults to None.
        Returns:
            None

        """

        # No information about experiment time is available with VFP600 files, so no conversion of samples to pd.Timestamp is possible.
        super().load(filename=filename, to_timestamp=False)

    def curve(self, curve=0):
        """retrieve chronoamperometry experiment data

        Args:
            curve (int, optional): curve to return (CHRONOA experiments typically only have 1 curve). Defaults to 1.

        Returns:
            pandas.DataFrame:
                - T: time, in seconds
                - Voltage: potential, in V
                - Current: current, in A
        """

        assert self.loaded, "DTA file not loaded. Run ChronoAmperometry.load()"
        df = self._curves[curve]
        df["T"] = df.index * self.sample_time
        return df[["T", "Voltage", "Current"]]

    @property
    def sample_time(self):
        """retrieve the programmed sample period

        Args:
            None.

        Returns:
            float: sample period of the potentiostat (in seconds), or 0 if no sample time recorded

        """
        freq = self._header.get("FREQ", None)

        return 1 / freq if freq else 0

    @property
    def sample_count(self, curve: int = 0):
        """compute the number of samples collected for the loaded chronoamperometry experiment

        Args:
            curve (int, optional): curve to return (CHRONOA experiments typically only have 1 curve). Defaults to 1.

        Returns:
            int: number of collected samples for the specified curve

        """

        return len(self._curves[curve - 1].index) if len(self._curves) > 0 else 0

    def _read_curve_data(self, fid: int):
        """helper function to process an EXPLAIN Table

        Args:
            fid (int): a file handle pointer to the table position in the data files
        Returns:
            keys (list): column identifier (e.g. Vf)
            units (list): column unit type (e.g. V)
            curve (DataFrame): Table data saved as a pandas Dataframe

        """
        pos = 0
        curve = fid.readline().strip() + "\n"  # grab header data
        if len(curve) <= 1:
            return [], [], pd.DataFrame()

        units = fid.readline().strip().split("\t")
        cur_line = fid.readline().strip()
        while not re.search(r"CURVE", cur_line):
            curve += cur_line + "\n"
            pos = fid.tell()
            cur_line = fid.readline().strip()
            if fid.tell() == pos:
                break

        curve = pd.read_csv(StringIO(curve), delimiter="\t", header=0)
        keys = curve.columns.values.tolist()
        units = units[1:]

        return keys, units, curve
