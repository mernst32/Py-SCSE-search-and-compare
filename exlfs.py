import os
import argparse


def scan_file(filename, query, copy=False):
    found = []
    with open(filename, 'r', encoding="utf-8") as ifile:
        if copy:
            line = ifile.readline().replace("//","",1)
            found.append(line.strip())
        for line in ifile:
            i = line.find(query)
            if i is not -1:
                line = line[i:]
                found.append(line.strip())
    return found


parser = argparse.ArgumentParser(
    description="Scans Java files for a given query and returns the lines containing said query starting "
        + "from the first occurrence.")
parser.add_argument('file', metavar='F', nargs=1, help="file to be scanned.")
parser.add_argument('query', metavar='Q', nargs=1, help="the searchquery.")
parser.add_argument('-d', '--dir', action='store_true', help="scan a directory instead of a file.")
parser.add_argument('-o', '--outfile', nargs=1, default=[""], help = "save output in given output file.")
parser.add_argument('-c', '--copyline', action='store_true', help = "copy first line of the scanned file(s)," 
                    + "removing comment characters like \"//\"")
args = parser.parse_args()
file = args.file[0]
query = args.query[0]
dir_flag = args.dir
out = args.outfile[0]
copy = args.copyline

if dir_flag:
    with os.scandir(file) as entries:
        if len(out) == 0:
            if copy:
                print("Filename,\"First Line\",StackOverflow Links\"")
            else:
                print("Filename,\"StackOverflow Links\"")
            for entry in entries:
                if entry.is_file():
                    delimeter = ','
                    result = scan_file(file + entry.name, query, copy)
                    if len(result) > 0:
                        if copy:
                            print(entry.name + "," + result[0] + "," + "\"" 
                                  + delimeter.join(result[1:]) + "\"")
                        else:
                            print(entry.name + "," + "\"" + delimeter.join(result) + "\"")
        else:
            with open(out, 'w', encoding="utf-8") as ofile:
                if copy:
                    ofile.write("Filename,\"First Line\",\"StackOverflow Links\"\n")
                else:    
                    ofile.write("Filename,\"StackOverflow Links\"\n")
                for entry in entries:
                    if entry.is_file():
                        delimeter = ','
                        result = scan_file(file + entry.name, query, copy)
                        if len(result) > 0:
                            if copy:
                                ofile.write(entry.name + "," + result[0] + "," + "\"" 
                                  + delimeter.join(result[1:]) + "\"\n")
                            else:
                                ofile.write(entry.name + "," + "\"" + delimeter.join(result) + "\"\n")
                
else:
    if len(out) == 0:
        if copy:
            print("Filename,\"First Line\",StackOverflow Links\"")
        else:
            print("Filename,\"StackOverflow Links\"")
        delimeter = ','
        result = scan_file(file, query, copy)
        if len(result) > 0:
            if copy:
                print(file + "," + result[0] + "," + "\"" 
                      + delimeter.join(result[1:]) + "\"")
            else:
                print(file + "," + "\"" + delimeter.join(result) + "\"")
    else:
        with open(out, 'w', encoding="utf-8") as ofile:
            if copy:
                ofile.write("Filename,\"First Line\",\"StackOverflow Links\"\n")
            else:    
                ofile.write("Filename,\"StackOverflow Links\"\n")
                
            delimeter = ','
            result = scan_file(file, query, copy)
            if len(result) > 0:
                if copy:
                    ofile.write(file + "," + result[0] + "," + "\"" 
                                + delimeter.join(result[1:]) + "\"\n")
                else:
                    ofile.write(file + "," + "\"" + delimeter.join(result) + "\"\n")
        
        
