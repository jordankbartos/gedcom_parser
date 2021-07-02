import argparse
import os

from .parse import GedcomParser

def parse_args():
    p= argparse.ArgumentParser(description="Convert GEDCOM files to CSV and CSV files to GEDCOM")

    p.add_argument(
        "--dir",
        "-direction",
        help="Which way to convert. GED2CSV or CSV2GED",
        action="store",
        nargs=1,
        type=str,
        choices=["GED2CSV", "CSV2GED"],
        required=True,
        dest="dir",
    )

    p.add_argument(
        "-f", "--f", "-from",
        help="File path to the file to be read",
        action="store",
        nargs=1,
        type=str,
        required=True,
        dest="fr",
    )

    p.add_argument(
        "-t", "--t", "-to",
        help="File path to the output file to be saved. Must not be an existant filepath.",
        action="store",
        nargs=1,
        type=str,
        required=True,
        dest="to",
    )

    return p.parse_args()


def validate_args(from_file:str, to_file:str):
    """Assert that to_file is not an existing filepath and from_file is an existing filepath"""
    ret = True
    if not os.path.exists(from_file):
        print("Invalid from file. File does not exist")
        ret = False
    if os.path.exists(to_file):
        print("Invalid to file. File already exists! I will not over-write a file!")
        ret = False
    return ret

def save_output(to_file):
    pass

def progress_callback(prompt:str, progress:float):
    """Dispalys a progress bar to the screen"""

if __name__ == "__main__":
    # Get and check args
    args = parse_args()
    direction = args.dir[0]
    from_file = args.fr[0]
    to_file = args.to[0]

    # validate file paths
    if not validate_args(from_file=from_file, to_file=to_file):
        exit(1)

    
    parser = GedcomParser(file_path=to_file)
    
    if direction == "GED2CSV":
        out_str = parser.gedcom_to_csv()

    elif direction == "CSV2GED":
        out_str = parser.csv_to_gedcom()

    else:
        raise ValueError(f"How did you sneak direction={direction} into the args?")

    exit(save_output(to_file))

