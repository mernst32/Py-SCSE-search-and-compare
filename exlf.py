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
            print("Filename,\"First Line\",\"Found Line\"")
        else:
            print("Filename,\"Found Line\"")
        result = search_file(file, query, copy)
        if len(result) > 0:
            if copy:
                for res in result[1:]:
                    print(file + "," + result[0] + "," + "\""
                          + res + "\"")
            else:
                for res in result:
                    print(file + "," + "\"" + res + "\"")
    else:
        with open(out, 'w', encoding="utf-8") as ofile:
            if verbose:
                print(os.path.join(file))
            if copy:
                ofile.write("Filename,\"First Line\",\"Found Line\"\n")
            else:
                ofile.write("Filename,\"Found Line\"\n")
            result = search_file(file, query, copy)
            if len(result) > 0:
                if copy:
                    for res in result[1:]:
                        ofile.write(file + "," + result[0] + "," + "\""
                                    + res + "\"\n")
                else:
                    for res in result:
                        ofile.write(file + "," + "\"" + res + "\"\n")


def scan_dirs(rootdir, query, copy=False, out="", verbose=False):
    if len(out) == 0:
        if copy:
            print("Filename,\"First Line\",\"Found Lines\"")
        else:
            print("Filename,\"Found Lines\"")
        for subdir, dir, files in os.walk(rootdir):
            for file in files:
                result = search_file(os.path.join(subdir, file), query, copy)
                if len(result) > 0:
                    if copy:
                        for res in result[1:]:
                            print(os.path.join(subdir, file) + "," + result[0] + "," + "\""
                                  + res + "\"")
                    else:
                        for res in result:
                            print(os.path.join(subdir, file) + "," + "\"" + res + "\"")
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
                            for res in result[1:]:
                                ofile.write(os.path.join(subdir, file) + "," + result[0] + "," + "\""
                                            + res + "\"\n")
                        else:
                            for res in result:
                                ofile.write(os.path.join(subdir, file) + "," + "\"" + res + "\"\n")


def handle_input(file, query, copyline, outfile, verbose):
    if args.recursive:
        scan_dirs(file, query, copyline, outfile, verbose)
    else:
        scan_file(file, query, copyline, outfile, verbose)


parser = argparse.ArgumentParser(
    description="Scans Java files for a given query and returns the lines containing said query starting "
                + "from the first occurrence.")
parser.add_argument('file', metavar='F', nargs=1, help="file to be scanned.")
parser.add_argument('query', metavar='Q', nargs=1, help="the searchquery.")
parser.add_argument('-r', '--recursive', action='store_true', help="scan a directory recursively.")
parser.add_argument('-o', '--output-file', nargs=1, default=[""], help="save output in given output file.")
parser.add_argument('-c', '--copy-line', action='store_true',
                    help="copy first line of the scanned file(s), removing comment characters like \"//\"")
parser.add_argument('-v', '--verbose', action='store_true', help="gives a more detailed output")

args = parser.parse_args()
handle_input(args.file[0], args.query[0], args.copy_line, args.output_file[0], args.verbose)
