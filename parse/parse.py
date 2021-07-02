import os
import sys
import re

def check_args():
    if len(sys.argv) == 2:
        if os.path.isfile(sys.argv[1]):
            ret = None
        else:
            ret = f"{sys.argv[1]} is not a file"
    else:
        ret = "What file should I examine?"
    return ret

if __name__ == "__main__":
    e = check_args()
    if e:
        print(f"usage error {e}")
    else:
        with open(sys.argv[1], "r") as f:
            lines = f.readlines()

    lines = [
        line[:-1]
        for line
        in lines
        if re.match(r"\d+ PLAC ..+", line)
    ]
