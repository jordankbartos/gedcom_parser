import re
from envparse import env
from typing import List, Optional, Union

GEDCOM_MAX_LINE_LENGTH = 80


class Line:
    """Represents a single line of a gedcom file

    A line has three parts: depth, tag, and tag_value. The third, tag_value, is optional.

    The format of a line is:
    {depth} {tag}[ {tag_value}]

    Seome examples are:
    0 INDI @Ixxx@
    1 DEAT
    2 DATE 1876
    """

    _LINE_RE = re.compile(r"^(?P<depth>[0-9]+) (?P<tag>[0-9A-Z_]+)(?: (?P<tag_value>.*))?$")

    def __init__(self, depth: Union[str, int], tag: str, tag_value: Optional[str] = None):
        r"""
        Parameters
        ----------
        depth: Union[str, int]
            The depth of the gedcom file line. Depth is the first part of a line entry. Typically a single digit 0-3
        tag: str
            The tag of the gedcome file line. E.g. "NAME", "BIRT", or "_PLAC"
        tag_value: Optional[str], default: None
            The value corresponding to the tag. E.g. "John \Cleese\"
        """
        self.depth = depth
        self.tag = tag
        self.tag_value = tag_value

    @staticmethod
    def get_parts_from_line(line: str) -> dict:
        r"""Accepts a gedcome line, parses its constituent parts and returns them as a dictionary

        Parameters
        ----------
        line: str

        Returns
        -------
        dict
            with keys "depth", "tag", and "tag_value". All values in the dict are strings, though "tag_value"
            may have a value of None.
        """

        m = Line._LINE_RE.match(line)

        if not m:
            raise ValueError(f"Invalid gedcom line recieved: {line}")

        return m.groupdict()

    @classmethod
    def from_str(cls, line: str):
        """Accepts a string and returns a Line object"""
        return cls(**cls.get_parts_from_line(line))

    def to_str(self) -> str:
        """Converts a line object to a string"""
        ret = f"{self.depth} {self.tag}"
        if self.tag_value is not None:
            ret = f"{ret} {self.tag_value}"
        return ret

    @staticmethod
    def get_depth_from_line(line: str) -> str:
        """Returns the depth value from a gedcom file line.

        E.g. A NAME line may look like '1 NAME Leonard Frank /Bartos/'. Here
        the depth is 1, meaning this is a first-order property of a base entry.

        E.g. A SURN line may look like '2 GIVN Leonard Frank'. Here the depth is
        2, meaning this is a second-order property of a base entry (a first-order
        property of a NAME line, probably).
        """
        return Line.get_parts_from_line(line=line)["depth"]

    @staticmethod
    def get_tag_from_line(line: str) -> str:
        """Returns the tag name from a gedcom file line. E.g. 'NAME', 'BIRT', 'FAMS'"""
        return Line.get_parts_from_line(line=line)["tag"]

    @staticmethod
    def get_tag_value_from_line(line: str) -> str:
        """Returns the value associated with a line in a gedcom file.
        If the line has no value, None is returned

        E.g. the line '1 NAME Dorothy Adela /Popp/` returns 'Dorothy Adela /Popp/`
        E.g. the line '1 BIRT' returns None
        """
        return Line.get_parts_from_line(line=line)["tag_value"]

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
    """Class to manage an entry. Where an entry is an entire INDI, FAM, or SOUR entry in a gedcom file"""

    _EMPTY_LINE_PLACEHOLDER = "<<NONE>>"
    _CONT_PLACEHOLDER = "<<CONT>>"
    _MISSING_DATA_PLACEHOLDER = "<<MISSING DATA>>"
    _CONT_RE = re.compile("^\d+ CONT (?P<value>.*)")
    _CONC_RE = re.compile("^\d+ CONC (?P<value>.*)")
    _EMPTY_LINE_RE = re.compile(r"^\d+ [A-Z_]{3,5}$")
    _FIRST_LINE_RE = re.compile(r"^0 (?P<id>@[IFS]\d+@) (?P<type>(?:INDI|FAM|SOUR))$")

    _DATE_TAG = "DATE"
    _ACTIVE_TAG_SEPARATOR = "+"
    _SUFFIX_SEPARATOR = "~"

    def __init__(self, lines: List[str], force_string_dates: bool, no_cont_conc: bool) -> None:
        f"""
        Parameters
        ----------
        lines: List[str]
            A list of strings where each item in the list is a line of a gedcome file pertaining to the entry.
            The order is assumed to be top -> bottom as if reading the gedcom file
        force_string_dates: bool
            A flag that, when True, will add a single-quote (') in front of DATE values. This should force excel to render
            these values as strings rather than attempt to interpret them as dates. Which it isn't super good at.
        no_cont_conc: bool
            A flag that, when True, disables attempts to preserve all CONT and CONC data. Instead a missing data
            string is put in place of CONT and CONC continued/concatenated values.
        """

        # the first line is not like the others. It contians the type of entry, and the id number
        self.ENTRY_DEBUG = env("VERBOSE_OUTPUT", cast=bool, default=False)

        # set self.id and self.type
        for k, v in self.get_first_line_dict(lines[0]).items():
            setattr(self, k, v)

        self.force_string_dates = force_string_dates
        self.no_cont_conc = no_cont_conc

        self.lines = lines[1:]

    @staticmethod
    def get_first_line_dict(line) -> dict:
        """Parses the first line of an entry and returns a dict with the groups defined in _FIRST_LINE_RE"""
        match = Entry._FIRST_LINE_RE.match(line)

        assert match

        return match.groupdict()

    @property
    def lines(self) -> List[str]:
        """Returns self.lines as a list of strings"""
        return self.add_cont_conc([l.to_str() for l in self._lines])

    @lines.setter
    def lines(self, val) -> None:
        """Sets self.lines. Stores lines as line objects under the hood"""
        if not isinstance(val, list):
            raise ValueError(f"lines must be an instance of list, go {type(val)}")
        elif not all([isinstance(v, str) for v in val]):
            raise ValueError("All lines must be string values")
        else:
            if self.no_cont_conc:
                self._lines = [Line.from_str(l) for l in self.remove_cont_conc(val)]
            else:
                self._lines = [Line.from_str(l) for l in self.collapse_cont_conc(val)]

    def remove_cont_conc(self, lines: List[str]) -> List[str]:
        r"""Removes CONT and CONC tags from a list of lines. Replaces them with a warning string

        Parameters
        ----------
        lines: List[str]
            A list of gedcom file lines

        Returns
        -------
        List[str]
            The processed gedcome file lines with CONT and CONC tags removed

        Example
        -------
        Input: ["0 NOTE This is a long", "1 CONT long long long ", "1 CONC long long long note"]
        Output: ["0 NOTE This is a long<<MISSING DATA>>"]
        """

        ret = []
        skip = False
        for i, line in enumerate(lines):

            # eliminate trailing newline characters
            if line.endswith("\n"):
                line = line[:-1]

            if self._CONT_RE.match(line) or self._CONC_RE.match(line):
                assert i > 0

                # the logic in the below else statement should only be executed once per series of CONT/CONCs. So,
                # skip is set to True on the first CONT/CONC found and it is handled. Then it is re-set to False
                # upon detecting the next line that does not contain a CONT/CONC tag
                if skip:
                    pass
                else:
                    prev_line = ret[-1]
                    skip = True

                    if len(prev_line) > GEDCOM_MAX_LINE_LENGTH - len(
                        self._MISSING_DATA_PLACEHOLDER
                    ):
                        # cut off the previous line so that the missing data placeholder can fit, then append the missing data placeholder
                        ret[
                            -1
                        ] = f"{prev_line[:GEDCOM_MAX_LINE_LENGTH - len(self._MISSING_DATA_PLACEHOLDER)]}{self._MISSING_DATA_PLACEHOLDER}"
                    elif self._EMPTY_LINE_RE.match(prev_line):
                        # Add the missing data placeholder, but make sure there is a space between it and the tag
                        prev_line = f"{prev_line} {self._MISSING_DATA_PLACEHOLDER}"
                    else:
                        # Add the missing data placeholder
                        prev_line = f"{prev_line}{self._MISSING_DATA_PLACEHOLDER}"
            else:
                skip = False
                ret.append(line)

        if self.ENTRY_DEBUG:
            print("REMOVE_CONT_CONC results:")
            for x in ret:
                print(f"\t{x}")

        return ret

    def collapse_cont_conc(self, lines: List[str]) -> List[str]:
        r"""Accepts a list of strings, combines lines that are contineud via CONT/CONC. Returns the modified list

        Parameters
        ----------
        lines: List[str]
            A list of gedcom file lines

        Returns
        -------
        List[str]
            The processed gedcome file lines with CONT and CONC folded up into the lines that they
            continued/concatenated

        Example
        -------
        Input: ["0 NOTE This is a long", "1 CONT long long long ", "1 CONC long long long note"]
        Output: ["0 NOTE This is a long<<CONT>>long long long long long long note"]
        """
        """Removes CONT and CONC tags in a list of lines by combining those lines into one line"""

        ret = []

        for i, line in enumerate(lines):

            # remove errant trailing newline characters
            if line.endswith("\n"):
                line = line[:-1]

            cont_match = self._CONT_RE.match(line)
            conc_match = self._CONC_RE.match(line)

            assert not (cont_match and conc_match)

            if cont_match:

                assert i != 0

                if self._EMPTY_LINE_RE.match(ret[-1]):
                    # if ret[-1] is nothing but a depth and tag, there needs to be a space before the CONT
                    ret[-1] = f"{ret[-1]} {self._CONT_PLACEHOLDER}{cont_match.groupdict()['value']}"
                else:
                    ret[-1] = f"{ret[-1]}{self._CONT_PLACEHOLDER}{cont_match.groupdict()['value']}"

            elif conc_match:
                assert i != 0
                assert not self._EMPTY_LINE_RE.match(ret[-1])
                # simply append the concatenated value. No need to check for empty tags as by definition, conc
                # tags are not applied to empty lines
                ret[-1] = f"{ret[-1]}{conc_match.groupdict()['value']}"
            else:
                # no processing necessary. Just append and move on
                ret.append(line)

        if self.ENTRY_DEBUG:
            print("COLLAPSE_CONT_CONC results:")
            for x in ret:
                print(f"\t{x}")

        return ret

    @staticmethod
    def add_cont_conc(lines: List[str]) -> List[str]:
        def get_tag_value_chunk(depth: Union[int, str], tag: str, tag_value: str):
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
                    or tag_value.find(self._CONT_PLACEHOLDER) != -1
                ):
                    newline_index = tag_value.find(self._CONT_PLACEHOLDER)

                    if newline_index != -1:
                        if (
                            len_depth + len_tag + num_spaces + newline_index
                        ) < GEDCOM_MAX_LINE_LENGTH:
                            ret = (
                                True,
                                "CONT",
                                tag_value.split(self._CONT_PLACEHOLDER)[0],
                                self._CONT_PLACEHOLDER.join(
                                    tag_value.split(self._CONT_PLACEHOLDER)[1:]
                                ),
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

        if self.ENTRY_DEBUG:
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

        # at minimum, id and type is needed
        ret = {"id": self.id, "tag_type": self.type}

        # a stack of active tags. The tags are concatenated together to form column headers
        active_tags = []

        # iterate through the Line objects directly
        for i, line in enumerate(self._lines):

            # Pop all no-longer-active tags off of the stack. The current line's depth - 1
            # indicates how many of the active tags are still relevant. (The current line contributes
            # an active tag. Thus, the length of active tags should always equal the depth of the line
            if line.depth <= len(active_tags) + 1:
                active_tags = active_tags[: (line.depth - 1)]
            active_tags.append(line.tag)

            # process tag_value. Tags with no value need a placeholder and date tags may need
            # adjusting depending on force_string_dates
            if line.tag_value is None:
                tag_value = self._EMPTY_LINE_PLACEHOLDER
            elif line.tag == self._DATE_TAG and self.force_string_dates and not tag.startswith("'"):
                tag_value = f"'{line.tag_value}"
            else:
                tag_value = line.tag_value

            # Ensure unique column headers. E.g. if there are two NAME entries in a record and each
            # has a GIVN sub-property, the dictionary should look like:
            # {
            #   "NAME+GIVN": "value",
            #   "NAME+GIVN_1": "other value",
            # }
            suffix = 0
            while self._ACTIVE_TAG_SEPARATOR.join(active_tags) in ret:
                suffix += 1
                active_tags[-1] = f"{line.tag}{self._SUFFIX_SEPARATOR}{suffix}"

            ret["+".join(active_tags)] = tag_value

        if self.ENTRY_DEBUG:
            print("--ENTRY AS DICT--")
            for k, v in ret.items():
                print(f"\t{k}: {v}")

        return ret
