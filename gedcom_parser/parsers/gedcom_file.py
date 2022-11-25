"""Contains the GedcomFile class which is the main entry point for parsing a .ged file"""
import logging
import pandas as pd
import re

from envparse import env
from typing import Union, Dict, List, Literal, Pattern

from .entry import Entry

LOG = logging.getLogger(__name__)


_INDI_REGEX = re.compile(r"^0 @I\d+@ INDI$")
"""Pattern object for identifying INDI (individual) record entries"""

_FAM_REGEX = re.compile(r"^0 @F\d+@ FAM$")
"""Pattern object for identifying FAM (family) record entries"""

_SOUR_REGEX = re.compile(r"^0 @S\d+@ SOUR$")
"""Pattern object for identifying SOUR (source) record entries"""


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
    get_all_records_csv(encoding="utf-8")
        Returns a dictionary of CSV format strings. Keys are "INDI", "FAM", and "SOUR".
    get_section_records_csv(section, encoding="utf-8")
        Returns the individual records formatted as a CSV
    """

    def __init__(
        self,
        gedcom_str: str,
        no_cont_conc: bool,
        force_string_dates: bool,
    ) -> None:

        self.gedcom_lines = gedcom_str.split("\n")
        self.no_cont_conc = no_cont_conc
        self.force_string_dates = force_string_dates

    def get_all_records_csv(self, encoding: str = "utf-8") -> Dict[str, str]:
        """Converts gedcom_str into separate CSV strings for indi, fam, and sour records

        Parameters
        ----------
        encoding : str, default="utf-8"
            encoding type to use when creating CSV strings.

        Returns
        -------
        Dict[str, str]
            A dictionary of entry type to csv strings with the following keys:
                - "INDI": individual entries csv string,
                - "FAM": family entries csv string,
                - "SOUR": source entries csv string,
        """
        return {
            "INDI": self.get_section_records_csv(section="indi", encoding=encoding),
            "FAM": self.get_section_records_csv(section="fam", encoding=encoding),
            "SOUR": self.get_section_records_csv(section="sour", encoding=encoding),
        }

    def get_section_records_csv(
        self, section: Literal["indi", "fam", "sour"], encoding: str = "utf-8"
    ) -> str:
        """Returns the records of a type as a CSV formatted string

        Parameters
        ----------
        section : Literal[&quot;indi&quot;, &quot;fam&quot;, &quot;sour&quot;]
            Which section-type to convert to CSV and return
        encoding : str, default="utf-8"
            encoding type to use when creating CSV strings.

        Returns
        -------
        str
        """
        entries = self._get_section_entries(section=section)
        df = self._get_entries_df(entries=entries)
        return self._convert_df_to_csv(df=df, encoding=encoding)

    def _get_entries_df(self, entries: List[Entry]) -> pd.DataFrame:
        """Converts a list of entries into a pandas DataFrame object

        Parameters
        ----------
        entries : List[Entry]

        Returns
        -------
        pd.DataFrame
        """
        return pd.DataFrame(x.to_col_name_dict() for x in entries)

    def _convert_df_to_csv(self, df: pd.DataFrame, encoding: str = "utf-8") -> str:
        """Accepts a dataframe and returns it formatted as a CSV string

        Parameters
        ----------
        df : pd.DataFrame
        encoding : str, default="utf-8"
            encoding type to use when creating CSV strings.

        Returns
        -------
        str
            A CSV-formatted string with the contents of df
        """
        return df.to_csv(header=True, index=False, encoding=encoding)

    def _get_section_entries(self, section: Literal["indi", "fam", "sour"]) -> List[Entry]:
        """Parses a section of the gedcom string and instantiates Entry items for the section

        Parameters
        ----------
        section : Literal[&quot;indi&quot;, &quot;fam&quot;, &quot;sour&quot;]
            Which section of the gedcom string to process

        Returns
        -------
        List[Entry]
            A list of Entry objects, one for each primary 0-level entry in the given section

        Raises
        ------
        RuntimeError
            if the section boundaries cannot be determined from the gedcom file. This indicates
            a mal-formed gedcom file.
        """
        ret = []

        start_line_index = self._get_section_start_index(section=section)
        end_line_index = self._get_section_end_index(section=section)
        if (start_line_index is None) ^ (end_line_index is None):
            raise RuntimeError(
                f"Cannot determine boundaries of {section} in the provided gedcom string.\n"
                "  Ensure that the GEDCOM file is formatted correctly and try again."
            )
        elif start_line_index:

            assert end_line_index is not None

            i = start_line_index
            while i <= end_line_index:
                j = i + 1

                while j < len(self.gedcom_lines) and not self.gedcom_lines[j].startswith("0"):
                    j += 1

                assert j <= end_line_index + 1
                assert self.gedcom_lines[i].startswith("0")
                assert self.gedcom_lines[j].startswith("0")

                LOG.debug(f"RECORD LINES {i}-{j}:")
                for k in range(i, j):
                    LOG.debug(f"\t{self.gedcom_lines[k]}")

                ret.append(
                    Entry(
                        lines=self.gedcom_lines[i:j],
                        force_string_dates=self.force_string_dates,
                        no_cont_conc=self.no_cont_conc,
                    )
                )
                i = j

        return ret

    def _get_section_start_index(self, section: Literal["indi", "fam", "sour"]) -> Union[int, None]:
        """Returns the section start line index

        Parameters
        ----------
        section : Literal[&quot;indi&quot;, &quot;fam&quot;, &quot;sour&quot;]
            Which section to seek the beginning of

        Returns
        -------
        Union[int, None]
            The line index (zero-indexed) of the gedcom string that marks the beginning of the
            requested section. If None is returned, this indicates the section is absent from
            the gedcom file
        """

        pattern = self._get_entry_regex_pattern(section=section)

        # find first instance of match
        ret = None
        for i, line in enumerate(self.gedcom_lines):
            if pattern.match(line):
                ret = i
                break

        LOG.debug(f"Start index of {section} determined: {ret}")
        return ret

    def _get_section_end_index(self, section: Literal["indi", "fam", "sour"]) -> int:
        """Returns the section end line index

        Parameters
        ----------
        section : Literal[&quot;indi&quot;, &quot;fam&quot;, &quot;sour&quot;]
            Which section to seek the end of

        Returns
        -------
        Union[int, None]
            The line index (zero-indexed) of the gedcom string that marks the end of the
            requested section. If None is returned, this indicates the section is absent from
            the gedcom file
        """
        pattern = self._get_entry_regex_pattern(section=section)

        ret = None

        i = len(self.gedcom_lines) - 1

        # start from the end of the gedcom file and work backwards searching for the last line that
        # matches the provided entry pattern
        end_found = False
        while i > 0 and not end_found:

            if pattern.match(self.gedcom_lines[i]):

                end_found = True
                i += 1

                # Now start working back forwards to find the end of this indi entry
                while i < len(self.gedcom_lines) and not self.gedcom_lines[i].startswith("0"):
                    i += 1
                    if self.gedcom_lines[i].startswith("0"):
                        ret = i - 1
            i -= 1

        LOG.debug(f"End index of {section} determined: {ret}")

        return ret

    def _get_entry_regex_pattern(self, section: Literal["indi", "fam", "sour"]) -> Pattern:
        """Returns a compiled regex pattern for matching 0-level entries for the given section type

        Parameters
        ----------
        section : Literal[&quot;indi&quot;, &quot;fam&quot;, &quot;sour&quot;]

        Returns
        -------
        Pattern
            a compiled regex pattern that will match 0-level entries of the requested type

        Raises
        ------
        ValueError
            if the provided section value does not match one of the available patterns
        """
        if section == "indi":
            ret = _INDI_REGEX
        elif section == "fam":
            ret = _FAM_REGEX
        elif section == "sour":
            ret = _SOUR_REGEX
        else:
            raise ValueError(f"invalid section type '{section}' provided")

        return ret
