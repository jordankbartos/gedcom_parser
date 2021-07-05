import pandas as pd
import re

from envparse import env
from typing import Union, List

from .line import Line

# CONT designates a line break within a record
# CONC continues a line w/o a line break

# sets the line length limit for an entry when CREATING a gedcom file. Entries too long to fit
# in one line are split using CONC
GEDCOM_MAX_LINE_LENGTH = 80

class Entry:
    def __init__(self, lines: List[str]):
        self.lines = lines

    @property
    def lines(self):
        return self.add_cont_conc(self._lines)

    @lines.setter
    def lines(self, val):
        if not isinstance(val, list):
            raise ValueError(f"lines must be an instance of list, go {type(val)}")
        elif not all([isinstance(v, str) for v in val]):
            raise ValueError("All lines must be string values")
        else:
            self._lines = self.remove_cont_conc(lines)

    @staticmethod
    def remove_cont_conc(lines: List[str]) -> List[str]:
        cont_re = re.compile("^\d+ CONT ")
        conc_re = re.compile("^\d+ CONC ")

        ret = []

        for i, line in enumerate(lines):
            # the first two cases should be impossible on the first line
            if line.endswith("\n"):
                line = line[:-1]
            
            if cont_re.match(line):
                assert i != 0
                ret[-1] = f"{ret[-1]}<<CONT>>{cont_re.split(line)[-1]}"
            elif conc_re.match(line):
                assert i != 0
                ret[-1] = f"{ret[-1]}{conc_re.split(line)[-1]}"
            else:
                ret.append(line)

        return ret

    @staticmethod
    def add_cont_conc(lines: List[str]) -> List[str]:

        def get_tag_value_chunk(depth, tag, tag_value):
            """Helper function to determine when and how to split a tag value
            Parameters
            ----------
            depth: Union[int, str]
                the depth value for the line being examined
            tag: str
                the tag for the line being examined. E.g. DATE, PLAC or BURI
            tag_value: str
                the rest of the line being examined

            Returns
            -------
            Tuple[bool, str, str, Union[str, None]]
                [0] - boolean: whether the tag_value needed to be split or not
                [1] - str: The tag for this line. Original tag, CONC, or CONT 
                [2] - str: the value of the split-off section of tag_value
                [3] - str|None: the remainder of tag_value
            """

            ret = (False, tag, tag_value, None)

            if tag_value is not None:
                len_depth = len(str(depth))
                len_tag = len(tag)
                len_tag_value = len(tag_value)
                num_spaces = 2

                if (
                    len_depth + len_tag + len_tag_value + num_spaces > GEDCOM_MAX_LINE_LENGTH
                    or tag_value.find("<<CONT>>") != -1
                ):
                    newline_index = tag_value.find("<<CONT>>")

                    if newline_index != -1:
                        if (len_depth + len_tag + num_spaces + newline_index) < GEDCOM_MAX_LINE_LENGTH:
                            ret = (
                                True,
                                "CONT",
                                tag_value.split("<<CONT>>")[0],
                                "<<CONT>>".join(tag_value.split("<<CONT>>")[1:]),
                            )
                        else:
                            ret = (
                                True,
                                "CONC",
                                tag_value[:GEDCOM_MAX_LINE_LENGTH - 1 - len_depth - len_tag - num_spaces],
                                tag_value[GEDCOM_MAX_LINE_LENGTH - 1- len_depth - len_tag - num_spaces:],
                            )
                    else:
                        ret = (
                            True,
                            "CONC",
                            tag_value[:GEDCOM_MAX_LINE_LENGTH - len_depth - len_tag - num_spaces],
                            tag_value[GEDCOM_MAX_LINE_LENGTH - len_depth - len_tag - num_spaces:],
                        )
                else:
                    pass
            else:
                pass
            return ret

        ret = []
        for i, line in enumerate(lines):

            depth = int(Line.get_depth_from_line(line))
            tag = Line.get_tag_from_line(line)
            tag_value = Line.get_tag_value_from_line(line)

            need_split, new_tag, tag_value, next_tag_value = get_tag_value_chunk(
                depth, tag, tag_value
            )

            ret.append(f"{depth} {tag} {tag_value}")

            while need_split:
                (
                    need_split,
                    new_tag,
                    prev_tag_value,
                    next_tag_value
                ) = get_tag_value_chunk(depth + 1, new_tag, next_tag_value)

                if prev_tag_value:
                    ret.append(f"{depth + 1} {new_tag} {prev_tag_value}")
                else:
                    ret.append(f"{depth + 1} {new_tag}")

        return ret


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

        i = start_of_indi_section
        while i < start_of_fam_section:
            j = i + 1
            while not self.gedcom_lines[j].startswith("0"):
                j += 1

            if self.PARSER_DEBUG:
                print('------------------------')
                print(f"INDI RECORD BETWEEN {i} AND {j}")
                print('ORIGINAL:')

                for k in range(i, j):
                    print(f"\t{self.gedcom_lines[k][:-1]}")
                print("REMOVE_CONT_CONC:")

            ls = Entry.remove_cont_conc(self.gedcom_lines[i:j])

            if self.PARSER_DEBUG:
                for x in ls:
                    print(f"\t{x}")
                print("ADD_CONT_CONC:")

            ls = Entry.add_cont_conc(ls)

            if self.PARSER_DEBUG:
                for x in ls:
                    print(f"\t{x}")

            i = j + 1

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
