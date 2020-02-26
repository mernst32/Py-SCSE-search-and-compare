import os
import argparse


def scan_file(filename, query):
    found = []
    with open(filename, 'r', encoding="utf-8") as ifile:
        for line in ifile:
            i = line.find(query)
            if i is not -1:
                line = line[i:]
                found.append(line.strip())
    return found


parser = argparse.ArgumentParser(
    description="Scans Java files for a given query and returns the lines containing said query.")
parser.add_argument('file', metavar='F', nargs=1, help="file to be scanned.")
parser.add_argument('query', metavar='Q', nargs=1, help="the searchquery.")
parser.add_argument('-d', '--dir', action='store_true', help="scan a directory instead of a file.")
parser.add_argument('-o', '--outfile', nargs=1, default=[""], help = "save output in given file")
args = parser.parse_args()
file = args.file[0]
query = args.query[0]
dir_flag = args.dir
out = args.outfile[0]

if dir_flag:
    with os.scandir(file) as entries:
        if len(out) == 0:
            print("filename,\"StackOverflow Links\"")
            for entry in entries:
                if entry.is_file():
                    delimeter = ','
                    result = delimeter.join(scan_file(file + entry.name, query))
                    if len(result) > 0:
                        print(entry.name + "," + "\"" + result + "\"")
        else:
            with open(out, 'w', encoding="utf-8") as ofile:
                ofile.write("filename,\"StackOverflow Links\"\n")
                for entry in entries:
                    if entry.is_file():
                        delimeter = ','
                        result = delimeter.join(scan_file(file + entry.name, query))
                        if len(result) > 0:
                            ofile.write(entry.name + "," + "\"" + result + "\"\n")
                
else:
    if len(out) == 0:
        print("filename,\"StackOverflow Links\"")
        delimeter = ','
        result = delimeter.join(scan_file(file, query))
        if len(result) > 0:
            print(file + "," + "\"" + result + "\"")
    else:
        with open(out, 'w', encoding="utf-8") as ofile:
            ofile.write("filename,\"StackOverflow Links\"\n")
            delimeter = ','
            result = delimeter.join(scan_file(file, query))
            if len(result) > 0:
                ofile.write(file + "," + "\"" + result + "\"\n")
        
        
