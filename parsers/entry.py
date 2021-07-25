import re
from envparse import env
from typing import Union, List


class Line:
    def __init__(self, depth, tag, tag_value):
        self.depth = depth
        self.tag = tag
        self.tag_value = tag_value

    @classmethod
    def from_str(cls, line):
        depth = cls.get_depth_from_line(line)
        tag = cls.get_tag_from_line(line)
        tag_value = cls.get_tag_value_from_line(line)

        return cls(depth=depth, tag=tag, tag_value=tag_value)

    def to_str(self):
        ret = f"{self.depth} {self.tag}"
        if self.tag_value is not None:
            ret = f"{ret} {self.tag_value}"
        return ret

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

        line_parts = line.split()
        if len(line_parts) < 2:
            raise ValueError(f"Cannot determine tag from line {line}.")
        else:
            return line_parts[1]

    @staticmethod
    def get_tag_value_from_line(line: str):
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

    def __init__(self, lines: List[str], force_string_dates, no_cont_conc):
        # the first line is not like the others. It contians the type of entry, and the id number
        self.ENTRY_DEBUG = env("VERBOSE_OUTPUT", cast=bool, default=False)

        self.type = self.get_type_from_line(lines[0])
        self.id = self.get_id_from_line(lines[0])
        self.force_string_dates = force_string_dates
        self.no_cont_conc = no_cont_conc

        self.empty_line_placeholder = "<<NONE>>"
        self.cont_placeholder = "<<CONT>>"
        self.missing_data_placeholder = "<<MISSING DATA>>"

        self.cont_re = re.compile("^\d+ CONT ")
        self.conc_re = re.compile("^\d+ CONC ")
        self.empty_line_re = re.compile(r"^\d+ \w{3,4}$")

        self.lines = lines[1:]

    @staticmethod
    def get_type_from_line(line):
        if self.ENTRY_DEBUG:
            assert re.match("^0 @[IFS]\d+@ (INDI|FAM|SOUR)$", line)
        return line.split()[2]

    @staticmethod
    def get_id_from_line(line):
        if self.ENTRY_DEBUG:
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
            if self.no_cont_conc:
                self._lines = [Line.from_str(l) for l in self.remove_cont_conc(val)]
            else:
                self._lines = [Line.from_str(l) for l in self.collapse_cont_conc(val)]

    def remove_cont_conc(self, lines: List[str]) -> List[str]:

        ret = []
        skip = False

        for i, line in enumerate(lines):
            if line.endswith("\n"):
                line = line[:-1]

            if self.cont_re.match(line) or self.conc_re.match(line):
                assert i > 0

                # don't do this repeatedly for consecutive CONTs or CONCs
                if skip:
                    pass
                else:
                    prev_line = ret[-1]

                    skip = True
                    if len(prev_line) > GEDCOM_MAX_LINE_LENGTH - len(self.missing_data_placeholder):
                        ret[
                            -1
                        ] = f"{ret[-1][:GEDCOM_MAX_LINE_LENGTH - len(self.missing_data_placeholder)]}{self.missing_data_placeholder}"
                    else:
                        if self.empty_line_re.match(ret[-1]):
                            ret[-1] = f"{ret[-1]} {self.missing_data_placeholder}"
                        else:
                            ret[-1] = f"{ret[-1]}{self.missing_data_placeholder}"
            else:
                skip = False
                ret.append(line)

        if self.ENTRY_DEBUG:
            print("REMOVE_CONT_CONC results:")
            for x in ret:
                print(f"\t{x}")
        return ret

    def collapse_cont_conc(self, lines: List[str]) -> List[str]:
        """Removes CONT and CONC tags in a list of lines by combining those lines into one line"""

        ret = []

        for i, line in enumerate(lines):
            # the first two cases should be impossible on the first line
            if line.endswith("\n"):
                line = line[:-1]

            if self.cont_re.match(line):
                assert i != 0
                # if ret[-1] is nothing but a depth and tag, there needs to be a space before the CONT
                if self.empty_line_re.match(ret[-1]):
                    ret[-1] = f"{ret[-1]} {self.cont_placeholder}{self.cont_re.split(line)[-1]}"
                else:
                    ret[-1] = f"{ret[-1]}{self.cont_placeholder}{self.cont_re.split(line)[-1]}"
            elif self.conc_re.match(line):
                assert i != 0
                ret[-1] = f"{ret[-1]}{self.conc_re.split(line)[-1]}"
            else:
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
                    or tag_value.find(self.cont_placeholder) != -1
                ):
                    newline_index = tag_value.find(self.cont_placeholder)

                    if newline_index != -1:
                        if (
                            len_depth + len_tag + num_spaces + newline_index
                        ) < GEDCOM_MAX_LINE_LENGTH:
                            ret = (
                                True,
                                "CONT",
                                tag_value.split(self.cont_placeholder)[0],
                                self.cont_placeholder.join(
                                    tag_value.split(self.cont_placeholder)[1:]
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

        ret = {"id": self.id, "tag_type": self.type}

        active_tags = []
        for i, line in enumerate(self._lines):

            if line.depth <= len(active_tags) + 1:
                active_tags = active_tags[: line.depth - 1]
            active_tags.append(line.tag)

            if line.tag_value is None:
                tag_value = self.empty_line_placeholder
            else:
                if self.force_string_dates and line.tag == "DATE":
                    tag_value = f"'{line.tag_value}"
                else:
                    tag_value = line.tag_value

            suffix = 0
            while "+".join(active_tags) in ret:
                suffix += 1
                active_tags[-1] = f"{line.tag}_{suffix}"

            ret["+".join(active_tags)] = tag_value

        if self.ENTRY_DEBUG:
            print("--ENTRY AS DICT--")
            for k, v in ret.items():
                print(f"\t{k}: {v}")

        return ret
