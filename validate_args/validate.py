import os


def validate_args(
    direction: str,
    gedcom_file: str,
    person_file: str,
    family_file: str,
    no_cont_conc: bool,
    force_string_dates: bool,
):
    """Assert that to_file is not an existing filepath and from_file is an existing filepath"""
    ret = []
    if direction == "GED2CSV":
        if not os.path.exists(gedcom_file):
            ret.append("Invalid gedcom file. File does not exist")
        if os.path.exists(person_file):
            ret.append("Invalid person file. File already exists! I will not over-write a file!")
        if os.path.exists(family_file):
            ret.append("Invalid family file. File already exists! I will not over-write a file!")
    elif direction == "CSV2GED":
        if not os.path.exists(person_file):
            ret.append("Invalid person file. File does not exist")
        if not os.path.exists(family_file):
            ret.append("Invalid family file. File does not exist")
        if os.path.exists(gedcom_file):
            ret.append("Invalid gedcom file. File already exists! I will not over-write a file!")
        if no_cont_conc:
            ret.append("Invalid option <no_cont_conc>. Cannot apply for direction <CSV2GED>.")
        if force_string_dates:
            ret.append("Invalid option <force_string_dates>. Cannot apply for direction <CSV2GED>.")
    else:
        ret.append("Invalid direction <{direction}>.")
    return ret
