import os


def validate_args(direction: str, gedcom_file: str, person_file: str, family_file: str):
    """Assert that to_file is not an existing filepath and from_file is an existing filepath"""
    ret = True
    if direction == "GED2CSV":
        if not os.path.exists(gedcom_file):
            print("Invalid gedcom file. File does not exist")
            ret = False
        if os.path.exists(person_file):
            print("Invalid person file. File already exists! I will not over-write a file!")
            ret = False
        if os.path.exists(family_file):
            print("Invalid family file. File already exists! I will not over-write a file!")
            ret = False
    elif direction == "CSV2GED":
        if not os.path.exists(person_file):
            print("Invalid person file. File does not exist")
            ret = False
        if not os.path.exists(family_file):
            print("Invalid family file. File does not exist")
            ret = False
        if os.path.exists(gedcom_file):
            print("Invalid gedcom file. File already exists! I will not over-write a file!")
            ret = False
    else:
        raise ValueError("Invalid direction")
    return ret
