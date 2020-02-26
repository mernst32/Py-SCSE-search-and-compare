import os
import argparse


def scan_file(filename, query):
    found = []
    sep = ','
    with open(filename, 'r', encoding="utf-8") as ifile:
        for line in ifile:
            if line.find(query) is not -1:
                found.append(line.strip())
    print(filename + " -> " + sep.join(found))


parser = argparse.ArgumentParser(
    description="Scans files for a given query and returns the lines containing said query.")
parser.add_argument('file', metavar='F', nargs=1, help="file to be scanned.")
parser.add_argument('query', metavar='Q', nargs=1, help="the searchquery.")
parser.add_argument('-d', '--dir', action='store_true', help="scan a directory instead of a file.")
args = parser.parse_args()
file = args.file[0]
query = args.query[0]
dir_flag = args.dir

if dir_flag:
    with os.scandir(file) as entries:
        for entry in entries:
            if entry.is_file():
                scan_file(file + entry.name, query)
else:
    scan_file(file, query)
