import os
import argparse
from datetime import datetime
from pathlib import Path


class Arguments:
    def __init__(self):
        self.dt = datetime.now().strftime("%Y%m%d-%H%M%S")

        # get and store command-line args
        self.raw_args = self.parse_args()

        # simple check to ensure arguments check out basically
        errors = self.validate_raw_args()

        if not errors:
            # derive file names if needed
            self.processed_args = self.process_raw_args()

            # Final validation. Files actually exist? etc..
            errors.extend(
                self.validate_args(
                    direction=self.processed_args["direction"],
                    gedcom_file=self.processed_args["gedcom_file"],
                    indi_file=self.processed_args["indi_file"],
                    fam_file=self.processed_args["fam_file"],
                    sour_file=self.processed_args["sour_file"],
                    no_cont_conc=self.processed_args["no_cont_conc"],
                    force_string_dates=self.processed_args["force_string_dates"],
                )
            )

        if errors:
            raise ValueError("\n".join([error for error in errors]))

        if self.ARGUMENTS_DEBUG:
            print("Set final arguments:")

        for k, v in self.processed_args.items():
            setattr(self, k, v)

            if self.ARGUMENTS_DEBUG:
                print(f"\t{k}: {v}")

        if self.ARGUMENTS_DEBUG:
            print("Arguments Accepted")

    def get_arg_value(self, arg):
        pass

    def process_raw_args(self):
        # Get and check args
        ret = {
            "direction": self.raw_args.dir[0],
            "indi_file": self.raw_args.indi_file,
            "fam_file": self.raw_args.fam_file,
            "sour_file": self.raw_args.sour_file,
            "gedcom_file": self.raw_args.gedcom_file,
            "verbose": self.raw_args.verbose,
            "no_cont_conc": self.raw_args.no_cont_conc,
            "force_string_dates": self.raw_args.force_string_dates,
        }

        self.ARGUMENTS_DEBUG = ret["verbose"]

        if self.ARGUMENTS_DEBUG:
            os.environ["VERBOSE_OUTPUT"] = "True"
            print("----Raw Arguments----")
            print(f"\tdirection: {ret['direction']}")
            print(f"\tindi_file: {ret['indi_file']}")
            print(f"\tfam_file: {ret['fam_file']}")
            print(f"\tsour_file: {ret['sour_file']}")
            print(f"\tgedcome_file: {ret['gedcom_file']}")
            print(f"\tno_cont_conc: {ret['no_cont_conc']}")
            print(f"\tforce_string_dates: {ret['force_string_dates']}")

        if ret["gedcom_file"] is None:
            ret["gedcom_file"] = self.derive_file_path(identifier="gedcom", ext=".ged")
        else:
            ret["gedcom_file"] = Path(ret["gedcom_file"][0])

        if ret["indi_file"] is None:
            ret["indi_file"] = self.derive_file_path(identifier="indi", ext=".csv")
        else:
            ret["indi_file"] = Path(ret["indi_file"][0])

        if ret["fam_file"] is None:
            ret["fam_file"] = self.derive_file_path(identifier="fam", ext=".csv")
        else:
            ret["fam_file"] = Path(ret["fam_file"][0])

        if ret["sour_file"] is None:
            ret["sour_file"] = self.derive_file_path(identifier="sour", ext=".sour")
        else:
            ret["sour_file"] = Path(ret["sour_file"][0])

        return ret

    def validate_args(
        self,
        direction: str,
        gedcom_file: str,
        indi_file: str,
        fam_file: str,
        sour_file: str,
        no_cont_conc: bool,
        force_string_dates: bool,
    ):
        """Assert that to_file is not an existing filepath and from_file is an existing filepath"""
        ret = []
        if direction == "GED2CSV":
            if not gedcom_file.exists():
                ret.append("Invalid gedcom file. File does not exist")
            if indi_file.exists():
                ret.append("Invalid indi file. File already exists! I will not over-write a file!")
            if fam_file.exists():
                ret.append("Invalid fam file. File already exists! I will not over-write a file!")
            if sour_file.exists():
                ret.append("Invalid sour file. File already exists! I will not over-write a file!")
        elif direction == "CSV2GED":
            if not indi_file.exists():
                ret.append("Invalid indi file. File does not exist")
            if not fam_file.exists():
                ret.append("Invalid fam file. File does not exist")
            if not sour_file.exists():
                ret.append("Invalid sour file. File does not exist")
            if gedcom_file.exists():
                ret.append(
                    "Invalid gedcom file. File already exists! I will not over-write a file!"
                )
            if no_cont_conc:
                ret.append("Invalid option <no_cont_conc>. Cannot apply for direction <CSV2GED>.")
            if force_string_dates:
                ret.append(
                    "Invalid option <force_string_dates>. Cannot apply for direction <CSV2GED>."
                )
        else:
            ret.append(f"Invalid direction <{direction}>.")
        return ret

    def validate_raw_args(self):
        """Performs basic checks to ensure arguments make some sort of sense"""
        ret = []

        if self.raw_args.dir[0] == "GED2CSV":
            if self.raw_args.gedcom_file is None:
                ret.append("Must provide a GEDCOM file path for direction 'GED2CSV'")
        elif self.raw_args.dir[0] == "CSV2GED":
            if self.raw_args.indi_file is None:
                ret.append("A INDI CSV file path must be provided for direction 'CSV2GED'")
            if self.raw_args.fam_file is None:
                ret.append("A FAM CSV file path must be provided for direction 'CSV2GED'")
            if self.raw_args.sour_file is None:
                ret.append("A SOUR CSV file path must be provided for direction 'CSV2GED'")
        else:
            ret.append(f"Received invalid direction {self.raw_args.dir}")

        return ret

    def parse_args(self):
        """ """
        p = argparse.ArgumentParser(
            description="Convert GEDCOM files to CSV and CSV files to GEDCOM"
        )

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
            required=False,
            dest="gedcom_file",
        )

        p.add_argument(
            "-i",
            "--indi-file",
            help="File path to the indi csv file to be read or generated",
            action="store",
            nargs=1,
            type=str,
            required=False,
            dest="indi_file",
        )

        p.add_argument(
            "-f",
            "--fam-file",
            help="File path to the fam csv file to be read or generated",
            action="store",
            nargs=1,
            type=str,
            required=False,
            dest="fam_file",
        )

        p.add_argument(
            "-s",
            "--sour-file",
            help="File path to the sour csv file to be read or generated",
            action="store",
            nargs=1,
            type=str,
            required=False,
            dest="sour_file",
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

    def derive_file_path(self, identifier, ext):
        parent = Path.home().joinpath("GedcomParser", self.dt)

        parent.mkdir(parents=True, exist_ok=True)
        ret = parent.joinpath(f"{identifier}_{self.dt}{ext}")
        if self.ARGUMENTS_DEBUG:
            print("Creating file path for:")
            print(f"\t{ret}")
        return ret
