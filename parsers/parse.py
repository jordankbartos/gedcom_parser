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
ENTRY_DEBUG = env("VERBOSE_OUTPUT", cast=bool, default=False)
PARSER_DEBUG = env("VERBOSE_OUTPUT", cast=bool, default=False)


class Entry:
    """Class to manage an entry. Where an entry is an entire INDI, FAM, or SOUR entry in a gedcom file"""

    def __init__(self, lines: List[str]):
        # the first line is not like the others. It contians the type of entry, and the id number
        self.type = self.get_type_from_line(lines[0])
        self.id = self.get_id_from_line(lines[0])
        self.lines = lines[1:]

    @staticmethod
    def get_type_from_line(line):
        assert re.match("^0 @[IFS]\d+@ (INDI|FAM|SOUR)$", line)
        return line.split()[2]

    @staticmethod
    def get_id_from_line(line):
        assert re.match("^0 @[IFS]\d+@ (INDI|FAM|SOUR)$", line)
        return line.split()[1]

    @property
    def lines(self):
        return self.add_cont_conc([l.to_str() for l in self._lines])

    @lines.setter
    def lines(self, val):
        if not isinstance(val, list):
            raise ValueError(f"lines must be an instance of list, go {type(val)}")
        elif not all([isinstance(v, str) for v in val]):
            raise ValueError("All lines must be string values")
        else:
            self._lines = [Line.from_str(l) for l in self.remove_cont_conc(val)]

    @staticmethod
    def remove_cont_conc(lines: List[str]) -> List[str]:
        """Removes CONT and CONC tags in a list of lines by combining those lines into one line"""

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

        if ENTRY_DEBUG:
            print("REMOVE_CONT_CONC results:")
            for x in ret:
                print(f"\t{x}")

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
                        if (
                            len_depth + len_tag + num_spaces + newline_index
                        ) < GEDCOM_MAX_LINE_LENGTH:
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
                                tag_value[
                                    : GEDCOM_MAX_LINE_LENGTH - 1 - len_depth - len_tag - num_spaces
                                ],
                                tag_value[
                                    GEDCOM_MAX_LINE_LENGTH - 1 - len_depth - len_tag - num_spaces :
                                ],
                            )
                    else:
                        ret = (
                            True,
                            "CONC",
                            tag_value[: GEDCOM_MAX_LINE_LENGTH - len_depth - len_tag - num_spaces],
                            tag_value[GEDCOM_MAX_LINE_LENGTH - len_depth - len_tag - num_spaces :],
                        )
                else:
                    pass
            else:
                pass

            return ret

        if ENTRY_DEBUG:
            print("ADD_CONT_CONC input:")
            for x in lines:
                print(f"\t{x}")

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
                (need_split, new_tag, prev_tag_value, next_tag_value) = get_tag_value_chunk(
                    depth + 1, new_tag, next_tag_value
                )

                if prev_tag_value:
                    ret.append(f"{depth + 1} {new_tag} {prev_tag_value}")
                else:
                    ret.append(f"{depth + 1} {new_tag}")

        if PARSER_DEBUG:
            print("ADD_CONT_CONC results:")
            for x in ret:
                print(f"\t{x}")

        return ret

    def to_col_name_dict(self):
        """Transform lines into a CSV-file-friendly dictionary of col-title:value pairs

        Tags are folded into eachother so that one entry can occupy a single row of the
        CSV file. E.g.

        0 @I42@ INDI
        1 NAME Leonard Frank /Bartos/
        2 GIVN Leonard Frank
        2 NSFX RPh
        1 SEX M
        1 _UID 4EF44217DF0F40419968D80B5CC5FE8491FB

        becomes

        {
            "type": "INDI",
            "id:" @I42@",
            "NAME": "Leonard Frand /Bartos/",
            "NAME+GIVN": "Leonard Frank",
            "NAME+NSFX": "RPh",
            "SEX": "M",
            "_UID": "4EF44217DF0F40419968D80B5CC5FE8491FB",
        }
        """

        ret = {"id": self.id, "tag_type": self.type}

        active_tags = []
        for i, line in enumerate(self._lines):

            if line.depth <= len(active_tags) + 1:
                active_tags = active_tags[: line.depth - 1]
            active_tags.append(line.tag)

            if line.tag_value is None:
                tag_value = "<<NONE>>"
            else:
                tag_value = line.tag_value

            ret["+".join(active_tags)] = tag_value

        if ENTRY_DEBUG:
            print("--ENTRY AS DICT--")
            for k, v in ret.items():
                print(f"\t{k}: {v}")

        return ret


class GedcomParser:
    def __init__(self, gedcom_file, family_file, person_file):
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

            # Make sure everything is looking ok
            assert i < j
            assert i >= start_of_indi_section
            assert j <= start_of_fam_section
            assert self.gedcom_lines[i].startswith("0")
            assert self.gedcom_lines[j].startswith("0")

            if PARSER_DEBUG:
                print("------------------------")
                print(f"INDI RECORD LINES {i}-{j}:")
                for k in range(i, j):
                    print(f"\t{self.gedcom_lines[k][:-1]}")

            self.indi_entries.append(Entry(lines=self.gedcom_lines[i:j]))
            x = self.indi_entries[-1].to_col_name_dict()

            i = j

        self.fam_entries = []
        i = start_of_fam_section
        while i < end_of_fam_section + 1:
            j = i + 1
            while j < len(self.gedcom_lines) and not self.gedcom_lines[j].startswith("0"):
                j += 1

            # Make sure everything is looking ok
            assert i < j
            assert i >= start_of_fam_section
            assert j <= end_of_fam_section + 1
            assert self.gedcom_lines[i].startswith("0")
            assert self.gedcom_lines[j].startswith("0")

            if PARSER_DEBUG:
                print("------------------------")
                print(f"FAM RECORD LINES {i}-{j}:")
                for k in range(i, j):
                    print(f"\t{self.gedcom_lines[k][:-1]}")
            self.fam_entries.append(Entry(lines=self.gedcom_lines[i:j]))

            i = j

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
