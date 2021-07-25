#!/usr/bin/python3
import os
from arguments import parse_args, validate_args


def save_output():
    return 0


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
    from parsers.gedcom_file import GedcomFile

    # validate file paths
    errors = validate_args( direction=direction, person_file=person_file, family_file=family_file, gedcom_file=gedcom_file, no_cont_conc=no_cont_conc, force_string_dates=force_string_dates,)

    if errors:
        for error in errors:
            print(f"\t{error}")
        exit(1)
    elif verbose:
        print("Validation succeeded")

    if direction == "GED2CSV":

        with open(gedcom_file, "r") as f:
            gedcom_str = f.read()

        parser = GedcomFile(
            gedcom_str=gedcom_str,
            no_cont_conc=no_cont_conc,
            force_string_dates=force_string_dates,
        )

        if verbose:
            print(f"Converting {gedcom_file} to CSV...")
        parts = parser.to_csv_strs()

        with open(person_file, "w") as f:
            f.write(parts["INDI"])

        with open(family_file, "w") as f:
            f.write(parts["FAM"])

    elif direction == "CSV2GED":
        exit(3)

        # with open(person_file, "r") as f:
        #    person_str = f.read()

        # with open(family_file, "r") as f:
        #    family_str = f.read()

        # parser = GedcomFile(
        #    gedcom_str=None,
        #    person_csv_str=None,
        #    family_csv_str=None,
        #    no_cont_conc=no_cont_conc,
        #    force_string_dates=force_string_dates,
        # )

        # if verbose:
        #    print(f"Converting {person_file} and {family_file} to GEDCOM...")
        # out_str = parser.csv_to_gedcom()

    else:
        raise ValueError(f"How did you sneak direction={direction} into the args?")

    exit(save_output())
