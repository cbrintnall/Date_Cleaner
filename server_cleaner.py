#! /usr/bin/python3

import sys

from datetime import datetime, timedelta

from os import listdir, stat, remove, chdir, rmdir
from os.path import isfile, isdir, abspath

from argparse import ArgumentParser

''' Globals '''
rm_date     = 0
limit       = 0
directories = 0
files       = 0
depth       = 0
depth_c     = 0

''' Flags below '''
FLAG_FIELD  = 0
FORCE       = 1
VERBOSE     = 2
NO_DIR      = 4
NO_FILES    = 8
COMPLETE    = 16
NOTIFY      = 32
ABSOLUTE    = 64

def main(argv):
    '''Setup argument processing'''
    parser = ArgumentParser(description="A utility for clearing out old files.")
    construct_args(parser)
    parse_cmds(parser.parse_args())


def check_flag(flag):
    global FLAG_FIELD
    return (FLAG_FIELD & flag) > 0

def construct_args(parser):
    ''' Constructs argument for the program '''
    parser.add_argument("rootdirectory", metavar="root", help="Parent node of directory tree")
    parser.add_argument("limit", metavar="limit", type=int,
                        help="Amount of days to check for before current date")
    parser.add_argument("-d", "--depth", help="How many folders deep (blank for unlimited)",
                        type=int, required=False)
    parser.add_argument("-f", help="Force removal (No prompts)",
                        action="store_true", required=False)
    parser.add_argument("-v", help="Gives a detailed report of operations",
                        action="store_true", required=False)
    parser.add_argument("-nd", help="Will not remove any directories",
                        action="store_true", required=False)
    parser.add_argument("-nf", help="Will not remove any files",
                        action="store_true", required=False)
    parser.add_argument("-c", help="Removes the root as well",
                        action="store_true", required=False)
    parser.add_argument("-n", help="Only notify, don't remove",
                        action="store_true", required=False)
    parser.add_argument("-abs", help="Gives the files absolute path when notifying",
                        action="store_true", required=False)

def parse_cmds(parsed):
    global FLAG_FIELD, FORCE, VERBOSE, NO_DIR, NO_FILES, COMPLETE, ABSOLUTE
    global files, directories, rm_date, depth

    if parsed.f:
        FLAG_FIELD |= FORCE

    if parsed.v:
        FLAG_FIELD |= VERBOSE

    if parsed.nd:
        FLAG_FIELD |= NO_DIR

    if parsed.nf:
        FLAG_FIELD |= NO_FILES

    if parsed.c:
        FLAG_FIELD |= COMPLETE

    if parsed.n:
        FLAG_FIELD |= NOTIFY

    if parsed.abs:
        FLAG_FIELD |= ABSOLUTE

    depth += parsed.depth

    rm_date = datetime.now() - timedelta(days=parsed.limit)

    try:
        directory = listdir(parsed.rootdirectory)
    except FileNotFoundError:
        print("Please enter a valid directory")
        sys.exit(1)

    chdir(parsed.rootdirectory)

    get_files(directory)

    if check_flag(COMPLETE):
        chdir("..")
        parent = parsed.rootdirectory.split("/")
        if check_flag(VERBOSE):
            print("Removing parent directory: {}.".format(parent[len(parent) - 1]))
        try:
            rmdir(parent[len(parent) - 1])
        except OSError:
            if check_flag(VERBOSE):
                print("WARNING: Couldn't remove directory: {}.".format(parent[len(parent) - 1]))
            directories -= 1
        directories += 1

    if check_flag(VERBOSE):
        print("====== REMOVE STATS ======")
        print("FILES: {}".format(files))
        print("DIRECTORIES: {}".format(directories))

def write_file(file):
    global FLAG_FIELD, ABSOLUTE
    if check_flag(ABSOLUTE):
        print("{}: {} is too old.".format(datetime.now(), abspath(file)))
    else:
        print("{}: {} is too old".format(datetime.now(), file))

def get_files(directory):
    global limit, directories, files, depth, rm_date, depth_c
    global FORCE, VERBOSE, NO_DIR, NO_FILES, NOTIFY

    for i in directory:
        if not check_flag(NO_FILES):
            if isfile(i):
                atime = datetime.fromtimestamp(stat(i).st_atime)
                if atime < rm_date:
                    if not check_flag(NOTIFY):
                        if not check_flag(FORCE):
                            remove_file = input("Remove {}? (y/n) ".format(abspath(i)))
                            if remove_file == "y" or remove_file == "yes":
                                remove(i)
                                files += 1
                                if check_flag(VERBOSE):
                                    print("Removed {}.".format(abspath(i)))
                        else:
                            remove(i)
                            if check_flag(VERBOSE):
                                print("Removed {}.".format(abspath(i)))
                            files += 1
                    else:
                        write_file(i)

        if not check_flag(NO_DIR):
            if isdir(i):
                if depth_c != depth:
                    depth_c += 1
                    directories += 1
                    if check_flag(VERBOSE):
                        print("Entering directory: {}.".format(i))
                    chdir(i)
                    get_files(listdir("."))
                    chdir("..")
                    try:
                        rmdir(i)
                    except OSError:
                        if check_flag(VERBOSE):
                            print("WARNING: Couldn't remove directory: {}.".format(i))
                        directories -= 1
                else:
                    if check_flag(VERBOSE):
                        print("Depth of {} hit, stopping.".format(depth_c))
                    break


if __name__ == "__main__":
    main(sys.argv)
