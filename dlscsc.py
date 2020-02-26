import urllib.request
import urllib.parse
import json
import os
import time
import math
from urllib.error import HTTPError
import argparse


def handle_err(url, cause, src, id_num):
    # print("ERROR while downloading " + str(id_num) + " saving msg in " + str(id_num) + ".error")
    try:
        os.makedirs("err/{0}".format(src))
    except FileExistsError as e:
        pass
    with open("err/{0}/{1}.error".format(src, id_num), 'w', encoding='utf-8') as ofile:
        ofile.write(url + '\n' + repr(cause))


def get_raw(url):
    # print("get data from "+url)
    contents = urllib.request.urlopen(url).read()
    return json.loads(contents.decode('utf-8'))


def get_page(search, page, per_page, src):
    params = {'q': search, 'lan': '23', 'p': page, 'per_page': per_page, 'src': src["id"]}
    url = "https://searchcode.com/api/codesearch_I/?" + urllib.parse.urlencode(params)
    try:
        raw_data = get_raw(url)
        results = raw_data["results"]
        id_list = []
        for result in results:
            id_list.append(result["id"])
        # print("getting " + str(len(results)) + " items from page " + str(page))
        for id_num in id_list:
            url = "https://searchcode.com/api/result/" + str(id_num) + "/"
            try:
                code = get_raw(url)["code"]
                lines = code.split('\n')
                with open("out/{0}/{1}.java".format(src["source"], id_num), 'w', encoding='utf-8') as ofile:
                    ofile.write("// https://searchcode.com/codesearch/raw/" + str(id_num) + "/" + '\n')
                    for line in lines:
                        ofile.write(line + '\n')
            except HTTPError as e:
                handle_err(url, e, src["source"], id_num)
            except json.decoder.JSONDecodeError as e:
                handle_err(url, e, src["source"], id_num)
        return len(id_list)
    except HTTPError as e:
        print("ERROR:Could not get data from " + url + ":" + repr(e))
        return 0


def get_java_code_from_repo(search, src, per_page):
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
        print("Downloading from " + src["source"] + ": ")
        for page in range(0, pages):
            dl_size = dl_size + get_page(search, page, per_page, src)

            if dl_size == 0:
                print("\tNothing to download!")
            else:
                prog = int(((page + 1) * bar_len) // pages)
                bar = '#' * prog + '.' * (bar_len - prog)
                print("\t" + str(int((prog / bar_len) * 100)) + "%" + " [" + bar + "] "
                      + str(dl_size) + "/" + str(total) + " Downloaded",
                      end='\r')
            time.sleep(1)
        print()
    except HTTPError as e:
        print("ERROR:Could not get data from " + url + ":" + repr(e))


def get_java_code(search, info, repo, per_page):
    params = {'q': search, 'lan': '23'}
    url = "https://searchcode.com/api/codesearch_I/?" + urllib.parse.urlencode(params)
    try:
        raw_data = get_raw(url)
        src_filters = raw_data["source_filters"]
        print("Found " + str(len(src_filters)) + " repo-source(s) with java files, that contain "
              + "the string \"" + search + "\"." + '\n')
        if not info:
            try:
                os.makedirs("out")
                os.makedirs("err")
            except FileExistsError as e:
                pass
            print("Starting download of the Java files...")
            if repo == -1:
                for src in src_filters:
                    try:
                        os.makedirs("out/{0}".format(src["source"]))
                    except FileExistsError as e:
                        pass
                    get_java_code_from_repo(search, src, per_page)
                    time.sleep(2)
            else:
                for src in src_filters:
                    if src["id"] == repo:
                        try:
                            os.makedirs("out/{0}".format(src["source"]))
                        except FileExistsError as e:
                            pass
                        get_java_code_from_repo(search, src, per_page)
            print("DONE WITH DOWNLOADS!")
        else:
            for src in src_filters:
                print(src["source"] + "[repo_id:" + str(src["id"]) + "]" + " with a total of " + str(src["count"])
                      + " result(s).")
                if src["count"] > (50 * per_page):
                    print("WARNING:The searchcode API only allows the download from up to 50 pages!")
                    print("\tSo this script will only be able to get " + str(50 * per_page) + " of the "
                          + str(src["count"]) + " files!")
    except HTTPError as e:
        print("ERROR:Could not get data from " + url + ":" + repr(e))


parser = argparse.ArgumentParser(
    description='Download Java Code from searchcode, that contain the given searchquery.')
parser.add_argument('query', metavar='Q', nargs=1, help="the searchquery.")
parser.add_argument('-i', '--info', action='store_true', help="only get the number of results.")
parser.add_argument('-r', '--repo', nargs=1, type=int, default=[-1],
                    help="specify the repo to search by giving the repo_id.")
args = parser.parse_args()
query = args.query[0]
info = args.info
repo = args.repo[0]
get_java_code(query, info, repo, 20)
