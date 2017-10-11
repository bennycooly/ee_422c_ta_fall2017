
import sys
import subprocess
import os


def main(argv):
    subprocess.run(["python", os.path.join(os.path.dirname(os.path.realpath(__file__)), "grader", "grader.py")] + argv[1:])

if __name__ == "__main__":
    main(sys.argv)

