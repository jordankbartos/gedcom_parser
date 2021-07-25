import pandas as pd
import re

from envparse import env
from typing import Union

from .entry import Entry

# CONT designates a line break within a record
# CONC continues a line w/o a line break

# sets the line length limit for an entry when CREATING a gedcom file. Entries too long to fit
# in one line are split using CONC
GEDCOM_MAX_LINE_LENGTH = 80
PARSER_DEBUG = env("VERBOSE_OUTPUT", cast=bool, default=False)


class GedcomFile:
    def __init__(
        self,
        gedcom_str,
        no_cont_conc,
        force_string_dates,
    ):
        self.gedcom_str = gedcom_str

        self.no_cont_conc = no_cont_conc
        self.force_string_dates = force_string_dates

        self.indi_regex = re.compile(r"^\d+ @I\d+@ INDI$")
        self.fam_regex = re.compile(r"^\d+ @F\d+@ FAM$")

    def to_csv_strs(self):
        """Converts self into CSV strings

        Parameters
        ----------
        None

        Returns
        -------
        A dictionary of entry type to csv strings with the following keys:
            - "INDI": individual entries csv string,
            - "FAM": family entries csv string,
            - "SOUR": source entries csv string,
        """
        # open the file and read lines
        self.gedcom_lines = self.gedcom_str.split("\n")

        # Find the start and stop for the indi and family sections
        start_of_indi_section = self.get_start_section("indi")
        end_of_indi_section = self.get_end_section("indi")
        start_of_fam_section = self.get_start_section("fam")
        end_of_fam_section = self.get_end_section("fam")

        if PARSER_DEBUG:
            print("--Determined these indexes for INDI and FAM sections--")
            print(f"\tfirst INDI index: {start_of_indi_section}")
            print(f"\tlast  INDI index: {end_of_indi_section}")
            print(f"\tfirst FAM  index: {start_of_fam_section}")
            print(f"\tlast  FAM  index: {end_of_fam_section}")

        self.indi_entries = []
        i = start_of_indi_section
        while i < start_of_fam_section:
            j = i + 1
            while j < len(self.gedcom_lines) and not self.gedcom_lines[j].startswith("0"):
                j += 1

            if PARSER_DEBUG:
                # Make sure everything is looking ok
                assert i < j
                assert i >= start_of_indi_section
                assert j <= start_of_fam_section
                assert self.gedcom_lines[i].startswith("0")
                assert self.gedcom_lines[j].startswith("0")

                print("------------------------")
                print(f"INDI RECORD LINES {i}-{j}:")
                for k in range(i, j):
                    print(f"\t{self.gedcom_lines[k][:-1]}")

            self.indi_entries.append(
                Entry(
                    lines=self.gedcom_lines[i:j],
                    force_string_dates=self.force_string_dates,
                    no_cont_conc=self.no_cont_conc,
                )
            )
            i = j

        self.fam_entries = []
        i = start_of_fam_section
        while i < end_of_fam_section + 1:
            j = i + 1
            while j < len(self.gedcom_lines) and not self.gedcom_lines[j].startswith("0"):
                j += 1

            if PARSER_DEBUG:
                # Make sure everything is looking ok
                assert i < j
                assert i >= start_of_fam_section
                assert j <= end_of_fam_section + 1
                assert self.gedcom_lines[i].startswith("0")
                assert self.gedcom_lines[j].startswith("0")

                print("------------------------")
                print(f"FAM RECORD LINES {i}-{j}:")
                for k in range(i, j):
                    print(f"\t{self.gedcom_lines[k][:-1]}")

            self.fam_entries.append(
                Entry(
                    lines=self.gedcom_lines[i:j],
                    force_string_dates=self.force_string_dates,
                    no_cont_conc=self.no_cont_conc,
                )
            )
            i = j

        self.indi_dicts = [i.to_col_name_dict() for i in self.indi_entries]
        self.indi_df = pd.DataFrame(self.indi_dicts)
        indi_csv_str = self.indi_df.to_csv()

        self.fam_dicts = [f.to_col_name_dict() for f in self.fam_entries]
        self.fam_df = pd.DataFrame(self.fam_dicts)
        fam_csv_str = self.fam_df.to_csv()

        return {
            "INDI": indi_csv_str,
            "FAM": fam_csv_str,
            "SOUR": "",
        }

    def get_start_section(self, section):
        """Returns the index of the line that begins the first Individual entry in the gedcom file"""
        ret = None

        # validate input
        if section == "indi":
            pattern = self.indi_regex
        elif section == "fam":
            pattern = self.fam_regex
        else:
            raise ValueError(f"invalid section type '{section}' provided")

        # find first instance of match
        for i, line in enumerate(self.gedcom_lines):
            if pattern.match(line):
                if PARSER_DEBUG:
                    assert line.startswith("0")
                ret = i
                break

        return ret

    def get_end_section(self, section):
        """Returns the index of the line that begins the last Individual entry in the gedcom file"""
        ret = None

        # validate input
        if section == "indi":
            pattern = self.indi_regex
        elif section == "fam":
            pattern = self.fam_regex
        else:
            raise ValueError(f"invalid section type '{section}' provided")

        i = len(self.gedcom_lines) - 1
        end_found = False
        # start from the end of the gedcom file and work backwards searching for the last
        # INDI entry
        while i > 0 and not end_found:

            line = self.gedcom_lines[i]
            if pattern.match(line):

                if PARSER_DEBUG:
                    assert line.startswith("0")

                # found the last indi entry
                end_found = True
                i += 1
                line = self.gedcom_lines[i]

                # Now start working back forwards to find the end of this indi entry
                while i < len(self.gedcom_lines) and not line.startswith("0"):
                    i += 1
                    line = self.gedcom_lines[i]
                    if line.startswith("0"):
                        # i is now set to the index of the line after the end of the last entry. So
                        # subtract one to get back to the last line of the previous entry
                        ret = i - 1
            i -= 1

        return ret
