#!/usr/bin/python3
import os
from arguments import Arguments
from parsers.gedcom_file import GedcomFile


def save_output():
    return 0


if __name__ == "__main__":

    # validate and get values from arguments
    args = Arguments()
    direction = args["direction"]
    person_file = args["person_file"]
    family_file = args["family_file"]
    source_file = args["source_file"]
    gedcom_file = args["gedcom_file"]
    verbose = args["verbose"]
    no_cont_conc = args["no_cont_conc"]
    force_string_dates = args["force_string_dates"]

    if direction == "GED2CSV":

        with open(gedcom_file, "r") as f:
            gedcom_str = f.read()

        gedcom_file = GedcomFile(
            gedcom_str=gedcom_str,
            no_cont_conc=no_cont_conc,
            force_string_dates=force_string_dates,
        )

        if verbose:
            print(f"Converting {gedcom_file} to CSV...")

        parts = gedcom_file.to_csv_strs()

        with open(person_file, "w") as f:
            f.write(parts["INDI"])

        with open(family_file, "w") as f:
            f.write(parts["FAM"])

        with open(source_file, "w") as f:
            f.write(parts["SOUR"])

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
