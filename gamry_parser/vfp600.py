import gamry_parser as parser
import pandas as pd
from pandas.api.types import is_numeric_dtype
import re
import locale
from io import StringIO


class VFP600(parser.GamryParser):
    """Load experiment data generated by Gamry VFP600 software (expected in EXPLAIN format, including header)"""

    def get_curve_data(self, curve=0):
        """ retrieve chronoamperometry experiment data

        Args:
            curve (int, optional): curve to return (CHRONOA experiments typically only have 1 curve). Defaults to 1.

        Returns:
            pandas.DataFrame:
                - T: time, in seconds
                - Voltage: potential, in V
                - Current: current, in A
        """

        assert self.loaded, 'DTA file not loaded. Run ChronoAmperometry.load()'
        df = self.curves[curve]
        df['T'] = df.index * self.get_sample_time()
        return df[['T', 'Voltage', 'Current']]

    def get_sample_time(self):
        """ retrieve the programmed sample period

        Args:
            None.

        Returns:
            float: sample period of the potentiostat (in seconds)

        """

        assert self.loaded, 'DTA file not loaded. Run ChronoAmperometry.load()'
        return 1/self.header['FREQ']

    def get_sample_count(self, curve=0):
        """ compute the number of samples collected for the loaded chronoamperometry experiment

        Args:
            curve (int, optional): curve to return (CHRONOA experiments typically only have 1 curve). Defaults to 1.

        Returns:
            int: number of collected samples for the specified curve

        """

        assert self.loaded, 'DTA file not loaded. Run ChronoAmperometry.load()'
        return len(self.curves[curve - 1].index)

    def read_curve_data(self, fid):
        """helper function to process an EXPLAIN Table

        Args:
            fid (int): a file handle pointer to the table position in the data files
        Returns:
            keys (list): column identifier (e.g. Vf)
            units (list): column unit type (e.g. V)
            curve (DataFrame): Table data saved as a pandas Dataframe
        
        """
        pos = 0
        curve = fid.readline().strip() + '\n'  # grab header data
        if len(curve) <= 1:
            return [], [], pd.DataFrame()

        units = fid.readline().strip().split('\t')
        cur_line = fid.readline().strip()
        while not re.search(r'CURVE', cur_line):
            curve += cur_line + '\n'
            pos = fid.tell()
            cur_line = fid.readline().strip()
            if fid.tell() == pos:
                break

        curve = pd.read_csv(StringIO(curve), '\t', header=0)
        keys = curve.columns.values.tolist()
        units = units[1:]

        return keys, units, curve

