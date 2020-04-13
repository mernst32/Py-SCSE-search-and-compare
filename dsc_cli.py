import urllib.request
import urllib.parse
import os
import time
from urllib.error import HTTPError
import argparse
from download_searchcode_files.core import get_raw, get_java_code_from_repo

data_folder = 'data'


def handle_input(search, info, repo, per_page):
    global data_folder
    dirname = os.path.dirname(__file__)
    out_folder = os.path.join(dirname, data_folder, 'out')
    err_folder = os.path.join(dirname, data_folder, 'err')
    params = {'q': search, 'lan': '23'}
    url = "https://searchcode.com/api/codesearch_I/?" + urllib.parse.urlencode(params)
    try:
        raw_data = get_raw(url)
        src_filters = raw_data["source_filters"]
        print("Found {0} repo-source(s) with java files, that contain the string \"{1}\".\n"
              .format(len(src_filters), search))
        if not info:
            try:
                os.makedirs(out_folder)
                os.makedirs(err_folder)
            except FileExistsError as e:
                pass
            print("Starting download of the Java files...")
            if repo == -1:
                for src in src_filters:
                    try:
                        os.makedirs("{0}/{1}".format(out_folder, src["source"]))
                    except FileExistsError as e:
                        pass
                    get_java_code_from_repo(search, src, per_page, out_folder, err_folder)
                    time.sleep(2)
            else:
                for src in src_filters:
                    if src["id"] == repo:
                        try:
                            os.makedirs("{0}/{1}".format(out_folder, src["source"]))
                        except FileExistsError as e:
                            pass
                        get_java_code_from_repo(search, src, per_page, out_folder, err_folder)
            print("DONE WITH DOWNLOADS!")
        else:
            for src in src_filters:
                print("{0}[repo_id: {1}] with a total of {2} restult(s)."
                      .format(src["source"], src["id"], src["count"]))
                if src["count"] > (50 * per_page):
                    print("WARNING:The searchcode API only allows the download from up to 50 pages!")
                    print("\tSo this script will only be able to get {0} of the {1} files!"
                          .format(50 * per_page, src["count"]))
    except HTTPError as e:
        print("ERROR:Could not get data from {0}: {1}".format(url, repr(e)))


parser = argparse.ArgumentParser(
    description='Download Java Code from searchcode, that contain the a StackOverflow Link.')
parser.add_argument('-i', '--info', action='store_true', help="only get the number of results.")
parser.add_argument('-r', '--repo', nargs=1, type=int, default=[-1],
                    help="specify the repo to search by giving the repo_id.")
args = parser.parse_args()

handle_input("stackoverflow.com", args.info, args.repo[0], 20)
