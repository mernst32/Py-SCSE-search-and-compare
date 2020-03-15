import os
import argparse


def search_file(filename, query, copy=False):
    found = []
    with open(filename, 'r', encoding="utf-8") as ifile:
        if copy:
            line = ifile.readline().replace("//", "", 1)
            found.append(line.strip())
        for line in ifile:
            i = line.find(query)
            if i is not -1:
                line = line[i:]
                chars = ";,)\""
                for char in chars:
                    line = line.replace(char, "")
                found.append(line.strip())
    return found


def scan_file(file, query, copy=False, out="", verbose=False):
    if len(out) == 0:
        if copy:
            print("Filename,\"First Line\",\"Found Lines\"")
        else:
            print("Filename,\"Found Lines\"")
        delimeter = ','
        result = search_file(file, query, copy)
        if len(result) > 0:
            if copy:
                print(file + "," + result[0] + "," + "\""
                      + delimeter.join(result[1:]) + "\"")
            else:
                print(file + "," + "\"" + delimeter.join(result) + "\"")
    else:
        with open(out, 'w', encoding="utf-8") as ofile:
            if verbose:
                print(os.path.join(file))
            if copy:
                ofile.write("Filename,\"First Line\",\"StackOverflow Links\"\n")
            else:
                ofile.write("Filename,\"StackOverflow Links\"\n")

            delimeter = ','
            result = search_file(file, query, copy)
            if len(result) > 0:
                if copy:
                    ofile.write(file + "," + result[0] + "," + "\""
                                + delimeter.join(result[1:]) + "\"\n")
                else:
                    ofile.write(file + "," + "\"" + delimeter.join(result) + "\"\n")


def scan_dirs(rootdir, query, copy=False, out="", verbose=False):
    if len(out) == 0:
        if copy:
            print("Filename,\"First Line\",\"Found Lines\"")
        else:
            print("Filename,\"Found Lines\"")
        for subdir, dir, files in os.walk(rootdir):
            for file in files:
                delimeter = ','
                result = search_file(os.path.join(subdir, file), query, copy)
                if len(result) > 0:
                    if copy:
                        print(os.path.join(subdir, file) + "," + result[0] + "," + "\""
                              + delimeter.join(result[1:]) + "\"")
                    else:
                        print(os.path.join(subdir, file) + "," + "\"" + delimeter.join(result) + "\"")
    else:
        with open(out, 'w', encoding="utf-8") as ofile:
            if copy:
                ofile.write("Filename,\"First Line\",\"Found Lines\"\n")
            else:
                ofile.write("Filename,\"Found Lines\"\n")
            for subdir, dir, files in os.walk(rootdir):
                for file in files:
                    if verbose:
                        print(os.path.join(subdir, file))
                    delimeter = ','
                    result = search_file(os.path.join(subdir, file), query, copy)
                    if len(result) > 0:
                        if copy:
                            ofile.write(os.path.join(subdir, file) + "," + result[0] + "," + "\""
                                        + delimeter.join(result[1:]) + "\"\n")
                        else:
                            ofile.write(os.path.join(subdir, file) + "," + "\"" + delimeter.join(result) + "\"\n")


parser = argparse.ArgumentParser(
    description="Scans Java files for a given query and returns the lines containing said query starting "
                + "from the first occurrence.")
parser.add_argument('file', metavar='F', nargs=1, help="file to be scanned.")
parser.add_argument('query', metavar='Q', nargs=1, help="the searchquery.")
parser.add_argument('-r', '--recursive', action='store_true', help="scan a directory recursively.")
parser.add_argument('-o', '--outfile', nargs=1, default=[""], help="save output in given output file.")
parser.add_argument('-c', '--copyline', action='store_true', help="copy first line of the scanned file(s),"
                                                                  + "removing comment characters like \"//\"")
parser.add_argument('-v', '--verbose', action='store_true', help="gives a more detailed output")

args = parser.parse_args()
file = args.file[0]
query = args.query[0]
r_flag = args.recursive
out = args.outfile[0]
copy = args.copyline
verbose = args.verbose

if r_flag:
    scan_dirs(file, query, copy, out, verbose)
else:
    scan_file(file, query, copy, out, verbose)
