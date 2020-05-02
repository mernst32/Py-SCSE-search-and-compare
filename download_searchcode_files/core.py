import string
import urllib.request
import urllib.parse
import json
import os
import time
import math
from urllib.error import HTTPError


def handle_err(url, cause, src, id_num, err_folder):
    """
    Handles any error that may occur, while getting data from url.

    :param url: the url that was being accessed while the error occurred. string
    :param cause: the cause of the error. ErrorMsg
    :param src: the repo src from which the code from the url comes from. string
    :param id_num: the id of the file on searchcode. string
    :param err_folder: the absolute path to the error folder. string
    """
    try:
        os.makedirs("{0}/{1}".format(err_folder, src))
    except FileExistsError as e:
        pass
    with open("{0}/{1}/{2}.error".format(err_folder, src, id_num), 'w', encoding='utf-8') as ofile:
        ofile.write(url + '\n' + repr(cause))


def get_raw(url):
    """
    Gets the JSON Data from the specified url after decoding it from utf-8.
    :param url: the specified url, a string.
    :return: a json object as specified by the searchcode api
    """
    # print("get data from "+url)
    contents = urllib.request.urlopen(url).read()
    return json.loads(contents.decode('utf-8'))


def get_page(search, page, per_page, src, out_folder, err_folder):
    """
    Get a result page from searchcode.

    :param search: string: the search query
    :param page: int: the page number
    :param per_page: int: the page size
    :param src: json object representing the repo from which the page will be downloaded
    :param out_folder: string: absolute path pointing to the output folder
    :param err_folder: string: absolute path pointing to the errormsg folder
    :return: the number of downloaded files
    """
    params = {'q': search, 'per_page': per_page, 'lan': '23', 'src': src["id"], 'page': page}
    url = "https://searchcode.com/api/codesearch_I/?" + urllib.parse.urlencode(params)
    try:
        raw_data = get_raw(url)
        results = raw_data["results"]
        if results is None:
            print("Error: Result for the request \'{0}\' was empty!".format(url))
            return 0
        id_list = []
        for result in results:
            id_list.append(result["id"])
        for id_num in id_list:
            url = "https://searchcode.com/api/result/" + str(id_num) + "/"
            try:
                code = get_raw(url)["code"]
                lines = code.split('\n')
                with open("{0}/{1}/{2}.java".format(out_folder, src["source"], id_num), 'w', encoding='utf-8') as ofile:
                    ofile.write("// https://searchcode.com/codesearch/raw/" + str(id_num) + "/" + '\n')
                    for line in lines:
                        ofile.write(line + '\n')
            except HTTPError as e:
                handle_err(url, e, src["source"], id_num, err_folder)
            except json.decoder.JSONDecodeError as e:
                handle_err(url, e, src["source"], id_num, err_folder)
        return len(id_list)
    except HTTPError as e:
        print("ERROR:Could not get data from {0}: {1}".format(url, repr(e)))
        return 0


def get_java_code_from_repo(search, src, per_page, out_folder, err_folder):
    """
    Get the java files that contain the search query from the specified repository type
    [Github, Bitbucket, GoogleCode,...].

    :param search: string: the searchquery
    :param src: JSON object representing the repo from which the code will be downloaded
    :param per_page: an int representing the number of files that should be downloaded per page
    :param out_folder: a string representing the absolute path to the download folder
    :param err_folder:  a string representing the absolute path to the error folder
    """
    params = {'q': search, 'lan': '23', 'src': src["id"]}
    url = "https://searchcode.com/api/codesearch_I/?" + urllib.parse.urlencode(params)
    try:
        raw_data = get_raw(url)
        total = raw_data["total"]
        if total > (50 * per_page):
            total = (50 * per_page)
        pages = int(math.ceil(total / per_page))
        bar_len = 50
        dl_size = 0
        print("Downloading from {0}: ".format(src["source"]))
        for page in range(0, pages):
            dl_size = dl_size + get_page(search, page, per_page, src, out_folder, err_folder)

            if dl_size == 0:
                print("\tNothing to download!")
            else:
                prog = int(((page + 1) * bar_len) // pages)
                bar = '#' * prog + '.' * (bar_len - prog)
                print("\t{0}% [{1}] {2}/{3} Downloaded".format(int((prog / bar_len) * 100), bar, dl_size, total),
                      end='\r')
            time.sleep(1)
        print()
    except HTTPError as e:
        print("ERROR:Could not get data from {0}: {1}".format(url, repr(e)))
