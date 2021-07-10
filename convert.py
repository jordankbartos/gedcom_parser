#!/usr/bin/python3
import os
from arguments import parse_args, validate_args


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
        gedcom_lines=gedcom_file,
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
