import urllib.request
import urllib.parse
import json
import os
import time
import math
from urllib.error import HTTPError


def handle_err(url, cause, src, id_num, err_folder):
    try:
        os.makedirs("{0}/{1}".format(err_folder, src))
    except FileExistsError as e:
        pass
    with open("{0}/{1}/{2}.error".format(err_folder, src, id_num), 'w', encoding='utf-8') as ofile:
        ofile.write(url + '\n' + repr(cause))


def get_raw(url):
    # print("get data from "+url)
    contents = urllib.request.urlopen(url).read()
    return json.loads(contents.decode('utf-8'))


def get_page(search, page, per_page, src, out_folder, err_folder):
    params = {'q': search, 'lan': '23', 'p': page, 'per_page': per_page, 'src': src["id"]}
    url = "https://searchcode.com/api/codesearch_I/?" + urllib.parse.urlencode(params)
    try:
        raw_data = get_raw(url)
        results = raw_data["results"]
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
