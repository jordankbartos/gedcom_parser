import logging
import pandas as pd
import re

from envparse import env
from typing import Union, Dict, List, Literal, Pattern

from .entry import Entry

LOG = logging.getLogger(__name__)


_INDI_REGEX = re.compile(r"^\d+ @I\d+@ INDI$")
# """Pattern object for identifying INDI (individual) record entries"""

_FAM_REGEX = re.compile(r"^\d+ @F\d+@ FAM$")
# """Pattern object for identifying FAM (family) record entries"""

_SOUR_REGEX = re.compile(r"^\d+ @S\d+@ SOUR$")
# """Pattern object for identifying SOUR (source) record entries"""


class GedcomFile:
    """Represents the contents of a Gedcom file.

    Takes the contents of a gedcom file and provides an interface for interpreting the contents
    and converting each section to CSV format.

    Parameters
    ----------
    gedcom_str : str
        The contents of a GEDCOM file as a string
    no_cont_conc : bool
        Whether or not to preserve data from CONT (continue) and CONC (concatenate) tags in the
        gedcom file
    force_string_dates : bool
        Date values are prepended with a single quote mark ("'") if True. This helps render dates
        as strings in Microsoft Excel, e.g.

    Methods
    -------
    to_csv_strs()
        Returns a dictionary

    """

    def __init__(
        self,
        gedcom_str: str,
        no_cont_conc: bool,
        force_string_dates: bool,
    ) -> None:

        self.gedcom_str = gedcom_str
        self.no_cont_conc = no_cont_conc
        self.force_string_dates = force_string_dates

    def get_indi_records_csv(self):
        return self.get_section_csv(section="indi", gedcom_lines=gedcom_lines)

    def get_sour_records_csv(self):
        return self.get_section_csv(section="sour", gedcom_lines=gedcom_lines)

    def get_fam_records_csv(self):
        return self.get_section_csv(section="fam", gedcom_lines=gedcom_lines)

    def to_csv_strs(self) -> Dict[str, str]:
        """Converts gedcom_str into separate CSV strings for indi, fam, and sour records

        Parameters
        ----------
        None

        Returns
        -------
        Dict[str, str]
            A dictionary of entry type to csv strings with the following keys:
                - "INDI": individual entries csv string,
                - "FAM": family entries csv string,
                - "SOUR": source entries csv string,
        """
        gedcom_lines = self.gedcom_str.split("\n")

        return {
            "INDI": self.get_indi_records_csv(),
            "FAM": self.get_fam_records_csv(),
            "SOUR": self.get_sour_records_csv(),
        }

    def get_section_csv(self, section: Literal["indi", "fam", "sour"], gedcom_lines: List[str]):
        entries = self._get_section_entries(section=section, gedcom_lines=gedcom_lines)
        df = self._get_section_df(entries=entries)
        return self._convert_df_to_csv(df=df)

    def _get_section_df(self, entries: List[Entry]) -> pd.DataFrame:
        return pd.DataFrame(x.to_col_name_dict() for x in entries)

    def _convert_df_to_csv(self, df: pd.DataFrame) -> str:
        return df.to_csv(index=False)

    def _get_section_entries(
        self, section: Literal["indi", "fam", "sour"], gedcom_lines: List[str]
    ) -> List[Entry]:
        start_line_index = self._get_section_start_index(section, gedcom_lines=gedcom_lines)
        end_line_index = self._get_section_end_index(section, gedcom_lines=gedcom_lines)

        ret = []
        if start_line_index is not None:
            assert end_line_index is not None
            i = start_line_index
            while i <= end_line_index:
                j = i + 1
                while j < len(gedcom_lines) and not gedcom_lines[j].startswith("0"):
                    j += 1

                # Make sure everything is looking ok
                assert i < j
                assert i >= start_line_index
                assert j <= end_line_index + 1
                assert gedcom_lines[i].startswith("0")
                assert gedcom_lines[j].startswith("0")

                LOG.debug(f"RECORD LINES {i}-{j}:")
                for k in range(i, j):
                    LOG.debug(f"\t{gedcom_lines[k]}")

                ret.append(
                    Entry(
                        lines=gedcom_lines[i:j],
                        force_string_dates=self.force_string_dates,
                        no_cont_conc=self.no_cont_conc,
                    )
                )
                i = j

        return ret

    def _get_section_start_index(
        self, section: Literal["indi", "fam", "sour"], gedcom_lines: List[str]
    ) -> Union[int, None]:
        """Returns the index of the line that begins the first Individual entry in the gedcom file"""

        pattern = self._get_pattern(section=section)

        # find first instance of match
        ret = None
        for i, line in enumerate(gedcom_lines):
            if pattern.match(line):
                ret = i
                assert line.startswith("0")
                break

        LOG.debug(f"Start index of {section} determined: {ret}")
        return ret

    def _get_section_end_index(
        self, section: Literal["indi", "fam", "sour"], gedcom_lines: List[str]
    ) -> int:
        """Returns the index of the line that begins the last Individual entry in the gedcom file"""
        pattern = self._get_pattern(section=section)

        ret = None

        i = len(gedcom_lines) - 1

        # start from the end of the gedcom file and work backwards searching for the last
        # INDI entry
        end_found = False
        while i > 0 and not end_found:

            if pattern.match(gedcom_lines[i]):

                assert gedcom_lines[i].startswith("0")

                # found the last indi entry
                end_found = True
                i += 1

                # Now start working back forwards to find the end of this indi entry
                while i < len(gedcom_lines) and not gedcom_lines[i].startswith("0"):
                    i += 1
                    if gedcom_lines[i].startswith("0"):
                        # i is now set to the index of the line after the end of the last entry. So
                        # subtract one to get back to the last line of the previous entry
                        ret = i - 1
            i -= 1

        LOG.debug(f"End index of {section} determined: {ret}")

        return ret

    def _get_pattern(self, section: Literal["indi", "fam", "sour"]) -> Pattern:
        if section == "indi":
            ret = _INDI_REGEX
        elif section == "fam":
            ret = _FAM_REGEX
        elif section == "sour":
            ret = _SOUR_REGEX
        else:
            raise ValueError(f"invalid section type '{section}' provided")

        return ret
