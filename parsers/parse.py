import pandas as pd
import re
from envparse import env


class Entry:
    def __init__(self):
        pass

class IndividualEntry(Entry):
    def __init__(self):
        pass

class FamilyEntry(Entry):
    def __init__(self):
        pass

class GedcomParser:
    def __init__(self, gedcom_file, family_file, person_file):
        self.PARSER_DEBUG = env("VERBOSE_OUTPUT", cast=bool, default=False)
        self.gedcom_file = gedcom_file
        self.family_file = family_file
        self.person_file = person_file
        self.indi_regex = re.compile(r"^\d+ @I\d+@ INDI$")
        self.fam_regex = re.compile(r"^\d+ @F\d+@ FAM$")

    def gedcom_to_csv(self):
        # open the file and read lines
        self.gedcom_lines = self.get_gedcom_lines()

        # Find the start and stop for the indi and family sections
        start_of_indi_section = self.get_start_indi()
        end_of_indi_section = self.get_end_indi()
        start_of_fam_section = self.get_start_fam()
        end_of_fam_section = self.get_end_fam()

        if self.PARSER_DEBUG:
            print("--Determined these indexes for INDI and FAM sections--")
            print(f"\tfirst INDI index: {start_of_indi_section}")
            print(f"\tlast  INDI index: {end_of_indi_section}")
            print(f"\tfirst FAM  index: {start_of_fam_section}")
            print(f"\tlast  FAM  index: {end_of_fam_section}")

        for i in range(start_of_indi_section, start_of_fam_section):
            pass




    def csv_to_gedcom(self):
        pass

    def handle_tag(self):
        pass

    def get_gedcom_lines(self):
        with open(self.gedcom_file, "r") as f:
            lines = f.readlines()
        assert len(lines) > 0
        return lines

    def get_start_indi(self):
        """Returns the index of the line that begins the first Individual entry in the gedcom file"""
        for i, line in enumerate(self.gedcom_lines):
            if self.indi_regex.match(line):
                assert line.startswith("0")
                return i
        raise ValueError(f"Could not determine first INDI entry in {self.gedcom_file}")
 
    def get_end_indi(self):
        """Returns the index of the line that begins the last Individual entry in the gedcom file"""
        ret = None

        i = len(self.gedcom_lines) - 1
        end_indi_found = False
        # start from the end of the gedcom file and work backwards searching for the last
        # INDI entry
        while i > 0 and not end_indi_found:

            line = self.gedcom_lines[i]
            if self.indi_regex.match(line):
                assert line.startswith("0")

                # found the last indi entry
                end_indi_found = True
                i += 1
                line = self.gedcom_lines[i]

                # Now start working back forwards to find the end of this indi entry
                while i < len(self.gedcom_lines) and not line.startswith("0"):
                    i += 1
                    line = self.gedcom_lines[i]
                    if line.startswith("0"):
                        ret = i - 1
            i -= 1
        if ret is None:
            raise ValueError(f"Could not determine last INDI entry in {self.gedco_file}")
        else:
            return ret

    def get_start_fam(self):
        """Returns the index of the line that begins the first Family entry in the gedcom file"""
        for i, line in enumerate(self.gedcom_lines):
            if self.fam_regex.match(line):
                assert line.startswith("0")
                return i
        raise ValueError(f"Could not determine first FAM entry in {self.gedcom_file}")

    def get_end_fam(self):
        """Returns the index of the line that begins the last Family entry in the gedcom file"""
        ret = None

        i = len(self.gedcom_lines) - 1
        end_fam_found = False
        # start from the end of the gedcom file and work backwards searching for the last
        # INDI entry
        while i > 0 and not end_fam_found:

            line = self.gedcom_lines[i]
            if self.fam_regex.match(line):
                assert line.startswith("0")

                # found the last fam entry
                end_fam_found = True
                i += 1
                line = self.gedcom_lines[i]

                # Now start working back forwards to find the end of this fam entry
                while i < len(self.gedcom_lines) and not line.startswith("0"):
                    i += 1
                    line = self.gedcom_lines[i]
                    if line.startswith("0"):
                        ret = i - 1
            i -= 1
        if ret is None:
            raise ValueError(f"Could not determine last INDI entry in {self.gedco_file}")
        else:
            return ret



        for i in range(len(self.gedcom_lines) - 1, -1, -1):
            line = self.gedcom_lines[i]
            if self.fam_regex.match(line):
                assert line.startswith("0")
                return i
        raise ValueError(f"Could not determine last INDI entry in {self.gedco_file}")
