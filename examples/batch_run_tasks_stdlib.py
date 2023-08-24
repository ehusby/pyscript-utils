#!/usr/bin/env python3

# Erik Husby, 2022

# The first line of this file is called a "shebang".
# In a Unix environment, this line tells the shell that
# this script should be run with Python (version 3) if
# the user attempts to execute it directly, for example
# with the command `./batch_run_tasks.py`.
# This script may also be run with the command
# `python3 batch_run_tasks.py` (or `python batch_run_tasks.py`,
# depending on the Python installation and/or contents of
# the shell's PATH environment variable).


# Put import statements at the top of the file
# so that their contents will be available when
# referenced at any point in the script.
import argparse
import glob
import os
import sys


# Making a custom type of exception to throw can be helpful
# both for debugging, and when it comes to error handling
# within the script with 'try-except' blocks as shown below.
class PythonEnvironmentError(Exception):
    def __init__(self, msg=""):
        super(Exception, self).__init__(msg)

# Checking the Python version is not necessarily something
# you want to or need to do in every script!
# We do it here to ensure the example script is run properly.
try:
    if sys.version_info[0] < 3:
        raise PythonEnvironmentError(
            "Python version must be >= 3, but was:\n---\n{0}\n---".format(sys.version)
        )
except PythonEnvironmentError:
    print("You may need to run this Python script through a"
          " different command prompt (Windows), or load a"
          " different Python module (Linux).")
    print("See the error message for details.")
    raise


def main():
    # Add any arguments you need to the bottom of this
    # code block, making sure to parse and validate
    # each argument as needed.
    parser = argparse.ArgumentParser(description=(
        "Perform a command on (a subset of) files in a directory in batch."))
    parser.add_argument('srcdir',
        help="Path to source directory.")
    parser.add_argument('dstdir',
        help="Path to destination directory.")
    parser.add_argument('--dryrun', action='store_true', default=False,
        help="Print actions without executing.")

    ## Parse arguments.
    args = parser.parse_args()
    # If path arguments were provided as "relative" paths
    # to the current working directory (e.g. ".\srcdir\")
    # then os.path.abspath will ensure these paths are
    # converted to "absolute" paths, which start at the
    # root folder/drive of the volume, such as
    # "C:\path\to\srcdir" on Windows or
    # "/mnt/path/to/srcdir" on Linux.
    srcdir = os.path.abspath(args.srcdir)
    dstdir = os.path.abspath(args.dstdir)
    print("srcdir = {}".format(srcdir))
    print("dstdir = {}".format(dstdir))

    ## Validate arguments.
    if not os.path.isdir(srcdir):
        parser.error("srcdir directory does not exist: {}".format(srcdir))
    if not os.path.isdir(dstdir):
        print("Creating destination directory: {}".format(dstdir))
        os.makedirs(dstdir)

    # Filter source files, usually by making use of the wildcard
    # character '*' to make a searchable filename pattern.
    filename_pattern = '*.txt'
    src_files_list = glob.glob(os.path.join(srcdir, filename_pattern))

    ntasks_total = len(src_files_list)
    print("Found {} files in srcdir with filename matching '{}' to work on".format(ntasks_total, filename_pattern))

    ntasks_i = 0
    for src_file in src_files_list:
        ntasks_i += 1

        # Set the path of the destination file.
        dst_file = os.path.join(dstdir, os.path.basename(src_file))
        # A path's "basename" is the filename of the file that
        # you usually see when you browse through files on your PC,
        # including the filename extension.

        # If this script takes a while to run, it's much better
        # to be able to see what's going on than to be in the dark.
        # Make good use of print statements like these for logging.
        print("Performing task ({}/{}): {} -> {}".format(
            ntasks_i,
            ntasks_total,
            src_file,
            dst_file
        ))

        if not args.dryrun:
            perform_task(src_file, dst_file)

    print("Done!")


def perform_task(src_file, dst_file):
    print("In perform_task: {} -> {}".format(src_file, dst_file))



# The following code block tells Python that when this
# script is executed, enter the function called `main`.
if __name__ == '__main__':
    main()
