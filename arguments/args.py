import os
import argparse


def validate_args(
    direction: str,
    gedcom_file: str,
    person_file: str,
    family_file: str,
    source_file: str,
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
        if os.path.exists(source_file):
            ret.append("Invalid source file. File already exists! I will not over-write a file!")
    elif direction == "CSV2GED":
        if not os.path.exists(person_file):
            ret.append("Invalid person file. File does not exist")
        if not os.path.exists(family_file):
            ret.append("Invalid family file. File does not exist")
        if not os.path.exists(source_file):
            ret.append("Invalid source file. File does not exist")
        if os.path.exists(gedcom_file):
            ret.append("Invalid gedcom file. File already exists! I will not over-write a file!")
        if no_cont_conc:
            ret.append("Invalid option <no_cont_conc>. Cannot apply for direction <CSV2GED>.")
        if force_string_dates:
            ret.append("Invalid option <force_string_dates>. Cannot apply for direction <CSV2GED>.")
    else:
        ret.append("Invalid direction <{direction}>.")
    return ret


def parse_args():
    p = argparse.ArgumentParser(description="Convert GEDCOM files to CSV and CSV files to GEDCOM")

    p.add_argument(
        "-d",
        "--direction",
        help="Which way to convert. GED2CSV or CSV2GED",
        action="store",
        nargs=1,
        type=str,
        choices=["GED2CSV", "CSV2GED"],
        required=True,
        dest="dir",
    )

    p.add_argument(
        "-g",
        "--gedcom",
        help="File path to the gedcom file to be read or generated",
        action="store",
        nargs=1,
        type=str,
        required=True,
        dest="gedcom_file",
    )

    p.add_argument(
        "-p",
        "--person-file",
        help="File path to the person csv file to be read or generated",
        action="store",
        nargs=1,
        type=str,
        required=True,
        dest="person_file",
    )

    p.add_argument(
        "-f",
        "--family-file",
        help="File path to the family csv file to be read or generated",
        action="store",
        nargs=1,
        type=str,
        required=True,
        dest="family_file",
    )

    p.add_argument(
        "-s",
        "--source-file",
        help="File path to the source csv file to be read or generated",
        action="store",
        nargs=1,
        type=str,
        required=True,
        dest="source_file",
    )
    p.add_argument(
        "-v",
        "--verbose",
        help="Verbose",
        action="store_true",
        dest="verbose",
    )

    p.add_argument(
        "--no-cont-conc",
        help="Do not attempt to handle CONT or CONC tags. Render <<MISSING DATA>> instead.",
        action="store_true",
        dest="no_cont_conc",
    )

    p.add_argument(
        "--force-string-dates",
        help="Prepend a `'` to the beginning of each date field value when converting GEDCOM to CSV.",
        action="store_true",
        dest="force_string_dates",
    )

    return p.parse_args()
