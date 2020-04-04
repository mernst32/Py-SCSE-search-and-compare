import argparse
from urllib.request import urlopen
import mosspy
import os
import logging
import time


def handle_input(user_id, base_folder):
    m = mosspy.Moss(user_id, "java")
    # get the repo folders
    sub_folders = os.listdir(base_folder)
    report_index = ["<html><head><title>Report Index</title></head>\n\t<body><h1>Report Index</h1><br>"]
    for sub_folder in sub_folders:
        curr_dir = os.path.join(base_folder, sub_folder)
        if os.path.isdir(curr_dir):

            # get the SC and SO code folders
            sub_sub_folders = os.listdir(curr_dir)
            total = len(sub_sub_folders)
            bar_len = 50
            print("{0}: {1} folders to submit.".format(curr_dir, total))
            print("Waiting 5 Seconds before going through the folder...")
            time.sleep(5)
            for count, sub_sub_folder in enumerate(sub_sub_folders):
                curr_dir = os.path.join(base_folder, sub_folder, sub_sub_folder)

                prog = int(((count + 1) * bar_len) // total)
                bar = '#' * prog + '.' * (bar_len - prog)
                print("\t{0}% [{1}] submitting java files from folder {2}/{3}".format(int((prog / bar_len) * 100), bar, count + 1, total),
                      end='\r')

                if os.path.isdir(curr_dir):
                    # reset submission files
                    m.files = []

                    # Adds all java files in the current directory as well as its subdirectories
                    wildcard = os.path.join(curr_dir, "*.java")
                    wildcard_in_sub = os.path.join(curr_dir, "*", "*.java")
                    m.addFilesByWildcard(wildcard)
                    m.addFilesByWildcard(wildcard_in_sub)

                    # Send files
                    try:
                        url = m.send()
                    except ConnectionError as e:
                        print("\r\nError occurred: {0}! Trying again in 60 seconds!".format(e))
                        time.sleep(60)
                        url = m.send()

                    # Download whole report locally including code diff links
                    mosspy.download_report(url, os.path.join(curr_dir, "report"), connections=8, log_level=logging.WARN)
                    report_index.append("\t<a href=\"{0}\">{0}</a><br>".format(
                        os.path.join(os.path.join(sub_folder, sub_sub_folder), "report", "index.html")))
                    time.sleep(.1)
            print("\t{0}% [{1}] {2}/{3} folders, whose java files were submitted"
                  .format("100", '#' * bar_len, total, total))

    report_index.append("</body></html>")
    report_path = os.path.join(base_folder, "links_to_reports.html")
    print("Creating report linking file {0}...".format(report_path))
    with open(report_path, mode='w', encoding='utf-8') as ofile:
        for line in report_index:
            ofile.write("{0}\n".format(line))


parser = argparse.ArgumentParser(
    description="MOSS CLI client for submitting java files to the service and downloading the report from the service "
                "locally. Will go through the sub folders of the given folder and submit the java files for plagiarism "
                "checks and download the reports locally, creating a linking file in the process")
parser.add_argument('user_id', metavar='U', nargs=1, help="Your user-id for the MOSS service.")
parser.add_argument('folder', metavar='F', nargs=1, help="The folder whose contents you want to submit.")
args = parser.parse_args()

handle_input(args.user_id[0], args.folder[0])
