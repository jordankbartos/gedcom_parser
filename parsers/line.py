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
