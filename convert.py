#!/usr/bin/python3
import logging
from arguments import Arguments
from parsers.gedcom_file import GedcomFile


if __name__ == "__main__":
    logging.basicConfig(filename="log.txt", level=logging.DEBUG, filemode="w")

    # validate and get values from arguments
    args = Arguments()
    direction = args.direction
    indi_file = args.indi_file
    fam_file = args.fam_file
    sour_file = args.sour_file
    gedcom_file = args.gedcom_file
    verbose = args.verbose
    no_cont_conc = args.no_cont_conc
    force_string_dates = args.force_string_dates

    if direction == "GED2CSV":

        with open(gedcom_file, "r", encoding="utf-8") as f:
            gedcom_str = f.read()

        gedcom_file = GedcomFile(
            gedcom_str=gedcom_str,
            no_cont_conc=no_cont_conc,
            force_string_dates=force_string_dates,
        )

        if verbose:
            print(f"Converting {gedcom_file} to CSV...")

        parts = gedcom_file.get_all_records_csv()

        with open(indi_file, "w") as f:
            f.write(parts["INDI"])

        with open(fam_file, "w") as f:
            f.write(parts["FAM"])

        with open(sour_file, "w") as f:
            f.write(parts["SOUR"])

    elif direction == "CSV2GED":
        exit(3)

        # with open(indi_file, "r") as f:
        #    indi_str = f.read()

        # with open(fam_file, "r") as f:
        #    fam_str = f.read()

        # parser = GedcomFile(
        #    gedcom_str=None,
        #    indi_csv_str=None,
        #    fam_csv_str=None,
        #    no_cont_conc=no_cont_conc,
        #    force_string_dates=force_string_dates,
        # )

        # if verbose:
        #    print(f"Converting {indi_file} and {fam_file} to GEDCOM...")
        # out_str = parser.csv_to_gedcom()

    else:
        raise ValueError(f"How did you sneak direction={direction} into the args?")

    exit(0)
