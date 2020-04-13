import os


def search_file(filename, query, copy=False):
    """
    Searches file for the given query.

    :param filename: the name of the file to be searched
    :param query: the query to search for
    :param copy: whether the first line of the file should be added to the found lines
    :return: a list of the found lines, after being sanitized
    """
    found = []
    with open(filename, 'r', encoding="utf-8") as ifile:
        if copy:
            line = ifile.readline().replace("//", "", 1)
            found.append(line.strip())
        for line in ifile:
            i = line.find(query)
            if i is not -1:
                line = line[i:]
                chars = ":;,()\"{}<>"
                tags = ["</a>", "<br/>", "<br>", "</pre>", "<pre>"]
                for tag in tags:
                    line = line.replace(tag, "")
                for char in chars:
                    line = line.replace(char, "")
                line = line.strip()
                j = line.find(" ")
                if j is not -1:
                    line = line[:j]
                found.append(line)
    return found


def scan_file(file, query, copy=False, out="", verbose=False):
    """
    Scans one file for the given query and save the found lines.

    :param file: the file to be scanned
    :param query: then query to be searched for
    :param copy: whether the first line of the file should be added
    :param out: Where to save the gotten lines
    :param verbose: print more data
    """
    if len(out) == 0:
        if copy:
            print("SC_Filepath,\"First Line\",Stackoverflow_Links")
        else:
            print("SC_Filepath,Stackoverflow_Links")
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
                print("scan: {0}".format(os.path.join(file)))
            if copy:
                ofile.write("SC_Filepath,\"First Line\",Stackoverflow_Links\n")
            else:
                ofile.write("SC_Filepath,Stackoverflow_Links\n")
            result = search_file(file, query, copy)
            if len(result) > 0:
                if copy:
                    for res in result[1:]:
                        ofile.write(file + "," + result[0] + "," + "\"" + res + "\"\n")
                else:
                    for res in result:
                        ofile.write(file + "," + "\"" + res + "\"\n")


def scan_dirs(rootdir, query, copy=False, out="", verbose=False):
    """
    Scan the files in the qiven rootdir for the query and save the found lines.

    :param rootdir: the dir whose files will be scanned
    :param query: the query to be searched for
    :param copy: whether the first line of the files should be copied
    :param out: where to save the gotten lines
    :param verbose: print more data
    :return:
    """
    if len(out) == 0:
        if copy:
            print("SC_Filepath,\"First Line\",Stackoverflow_Links")
        else:
            print("SC_Filepath,Stackoverflow_Links")
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
                ofile.write("SC_Filepath,\"First Line\",Stackoverflow_Links\n")
            else:
                ofile.write("SC_Filepath,Stackoverflow_Links\n")
            for subdir, dir, files in os.walk(rootdir):
                for file in files:
                    if verbose:
                        print("scan: {0}".format(os.path.join(subdir, file)))
                    delimeter = ','
                    result = search_file(os.path.join(subdir, file), query, copy)
                    if len(result) > 0:
                        if copy:
                            for res in result[1:]:
                                ofile.write(os.path.join(subdir, file) + "," + result[0] + "," + "\"" + res + "\"\n")
                        else:
                            for res in result:
                                ofile.write(os.path.join(subdir, file) + "," + "\"" + res + "\"\n")