#!/usr/bin/python3
import argparse
import os

from validate_args.validate import validate_args


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
        help="File path to the familycsv file to be read or generated",
        action="store",
        nargs=1,
        type=str,
        required=True,
        dest="family_file",
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


def save_output():
    return 1


if __name__ == "__main__":
    # Get and check args
    args = parse_args()
    direction = args.dir[0]
    person_file = args.person_file[0]
    family_file = args.family_file[0]
    gedcom_file = args.gedcom_file[0]
    verbose = args.verbose
    no_cont_conc = args.no_cont_conc
    force_string_dates = args.force_string_dates

    if verbose:
        os.environ["VERBOSE_OUTPUT"] = "True"
        print("--Arguments--")
        print(f"\tdirection: {direction}")
        print(f"\tperson_file: {person_file}")
        print(f"\tfamily_file: {family_file}")
        print(f"\tgedcome_file: {gedcom_file}")
        print(f"\tno_cont_conc: {no_cont_conc}")
        print(f"\tforce_string_dates: {force_string_dates}")

    # have to wait to import this until after env variables are set conditionally
    from parsers.parse import GedcomParser

    # validate file paths
    errors = validate_args(
        direction=direction,
        person_file=person_file,
        family_file=family_file,
        gedcom_file=gedcom_file,
        no_cont_conc=no_cont_conc,
        force_string_dates=force_string_dates,
    )

    if errors:
        for error in errors:
            print(f"\t{error}")
        exit(1)
    elif verbose:
        print("Validation succeeded")

    parser = GedcomParser(
        gedcom_file=gedcom_file,
        person_file=person_file,
        family_file=family_file,
        no_cont_conc=no_cont_conc,
        force_string_dates=force_string_dates,
    )

    if direction == "GED2CSV":
        if verbose:
            print(f"Converting {gedcom_file} to CSV...")
        out_str = parser.gedcom_to_csv()

    elif direction == "CSV2GED":
        if verbose:
            print(f"Converting {person_file} and {family_file} to GEDCOM...")
        out_str = parser.csv_to_gedcom()

    else:
        raise ValueError(f"How did you sneak direction={direction} into the args?")

    exit(save_output())
