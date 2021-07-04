import pandas as pd
import re
from envparse import env
from typing import Union, List

# CONT designates a line break within a record
# CONC continues a line w/o a line break

# sets the line length limit for an entry when CREATING a gedcom file. Entries too long to fit
# in one line are split using CONC
GEDCOM_MAX_LINE_LENGTH = 80

class Line:

    def __init__(self, line: str):
        self.line = line
        self.depth = self.get_depth_from_line(self.line)
        self.tag = self.get_tag_from_line(self.line)
        self.tag_value = self.get_tag_value_from_line(self.line)

    @staticmethod
    def get_depth_from_line(line: str):
        """Returns the depth value from a gedcom file line.

        E.g. A NAME line may look like '1 NAME Leonard Frank /Bartos/'. Here
        the depth is 1, meaning this is a first-order property of a base entry.

        E.g. A SURN line may look like '2 GIVN Leonard Frank'. Here the depth is
        2, meaning this is a second-order property of a base entry (a first-order
        property of a NAME line, probably).
        """

        ret = line.split()[0]
        if not ret.isdigit():
            raise ValueError(
                f"Line appears to have an invalid depth value."
                f"Line should start with an integer. Line={line}"
            )
        else:
            return ret

    @staticmethod
    def get_tag_from_line(line: str):
        """Returns the tag name from a gedcom file line. E.g. 'NAME', 'BIRT', 'FAMS'"""

        print(line)
        line_parts = line.split()
        if len(line_parts) < 2:
            raise ValueError(f"Cannot determine tag from line {line}.")
        else:
            return line_parts[1]

    @staticmethod
    def get_tag_value_from_line(line):
        """Returns the value associated with a line in a gedcom file.
        If the line has no value, None is returned

        E.g. the line '1 NAME Dorothy Adela /Popp/` returns 'Dorothy Adela /Popp/`
        E.g. the line '1 BIRT' returns None
        """

        ret = None
        if len(line.split()) > 2:
            ret = " ".join(line.split()[2:])
        return ret

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, val):
        if not isinstance(val, str):
            raise ValueError(f"invalid line type of {type(val)}")
        else:
            self._line = val

    @property
    def depth(self):
        return self._depth

    @depth.setter
    def depth(self, val):
        print(val)
        if not isinstance(val, (str, int)):
            raise ValueError(f"invalid depth type of {type(val)}")
        else:
            self._depth = int(val)

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, val):
        if not isinstance(val, str):
            raise ValueError(f"invalid tag type of {type(val)}")
        else:
            self._tag = val

    @property
    def tag_value(self):
        return self._tag_value

    @tag_value.setter
    def tag_value(self, val):
        if val is not None and not isinstance(val, str):
            raise ValueError(f"invalid tag_value type of {type(val)}")
        else:
            self._tag_value = val

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
            if not int(Line.get_depth_from_line(self.gedcom_lines[i])) == 0:
                l = Line(self.gedcom_lines[i])
                print("made a line obj!")

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
