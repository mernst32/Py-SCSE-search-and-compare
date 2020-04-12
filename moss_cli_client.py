import argparse
import csv
from urllib.error import URLError
from urllib.request import urlopen
import mosspy
import os
import logging
import time
import threading
import queue
from bs4 import BeautifulSoup

lock = threading.Lock()
report_links_file = r'links_to_reports.html'
report_csv_file = r'moss_report.csv'


def dl_worker(q, base_url, dest_path, traversed):
    while True:
        url = q.get()
        if url is None:
            break
        try:
            response = urlopen(url)
        except URLError:
            time.sleep(60)
            q.put(url)
            q.task_done()
            break
        with lock:
            traversed.append(url)
        basename = os.path.basename(url)
        html = response.read()
        soup = BeautifulSoup(html, 'lxml')
        children = soup.find_all('frame')
        edges = []
        for child in children:
            if child.has_attr('src'):
                edge = child.get('src')
                if edge.find("match") != -1:
                    child['src'] = os.path.basename(edge)
                    if edge == child['src']:
                        edge = base_url + edge
                    if edge not in edges:
                        with lock:
                            if edge not in traversed:
                                edges.append(edge)
        with open(os.path.join(dest_path, basename), mode='wb') as ofile:
            ofile.write(soup.encode(soup.original_encoding))
        for edge in edges:
            q.put(edge)
        q.task_done()


def dl_report(report_url, dest_path, max_connections=4):
    if len(report_url) == 0:
        raise Exception("Empty url supplied")

    if not os.path.exists(dest_path):
        os.makedirs(dest_path)

    base_url = "{0}/".format(report_url)
    try:
        response = urlopen(report_url)
    except URLError as e:
        print("\r\nURLError: {0}!".format(e))
        print("Trying again in 60 seconds!", end='\r')
        time.sleep(60)
        response = urlopen(report_url)
    html = response.read()
    soup = BeautifulSoup(html, 'lxml')

    children = soup.find_all('a')
    edges = []
    traversed = []
    for child in children:
        if child.has_attr('href'):
            edge = child.get('href')
            if edge.find("match") != -1:
                child['href'] = os.path.basename(edge)
                if edge == child['href']:
                    edge = base_url + edge
                if edge not in edges:
                    edges.append(edge)
    traversed.append(report_url)
    url_queue = queue.Queue()
    threads = []
    num_of_threads = min(max_connections, len(edges))
    for i in range(num_of_threads):
        worker = threading.Thread(target=dl_worker, args=[url_queue, base_url, dest_path, traversed])
        worker.setDaemon(True)
        worker.start()
        threads.append(worker)
    for edge in edges:
        url_queue.put(edge)
    with open(os.path.join(dest_path, "index.html"), mode='wb') as ofile:
        ofile.write(soup.encode(soup.original_encoding))
    url_queue.join()
    for i in range(num_of_threads):
        url_queue.put(None)
    for t in threads:
        t.join()




def parse_moss_reports(join_file):
    global report_links_file
    global report_csv_file
    links = []
    print("Getting paths to reports from file {0}...".format(report_links_file))
    with open(report_links_file, mode='r', encoding='utf-8') as html:
        soup = BeautifulSoup(html, 'lxml')
        a_elems = soup.find_all('a')
        for a_elem in a_elems:
            if a_elem.has_attr('href'):
                links.append(a_elem['href'])

    total = len(links)
    bar_len = 50
    rows = []
    basic_keys = ['File_1', 'File_2', 'Lines_Matched', 'Code_Similarity']
    print("Following the gathered paths to the reports and parsing those...")
    for count, link in enumerate(links):

        prog = int(((count + 1) * bar_len) // total)
        bar = '#' * prog + '.' * (bar_len - prog)
        print("\t{0}% [{1}] parsing report {2}/{3}"
              .format(int((prog / bar_len) * 100), bar, count + 1, total),
              end='\r')

        with open(link, mode='r', encoding='utf-8') as html:
            soup = BeautifulSoup(html, 'lxml')
            tr_elems = soup.find_all('tr')
            for tr_elem in tr_elems:
                td_elems = tr_elem.find_all('td')
                if len(td_elems) == 3:
                    file_1 = None
                    file_2 = None
                    file_link_1 = td_elems[0].find_all('a')
                    file_link_2 = td_elems[1].find_all('a')
                    if len(file_link_1) == 1:
                        file_1 = str(file_link_1[0].contents[0])
                    if len(file_link_2) == 1:
                        file_2 = str(file_link_2[0].contents[0])
                    lines_matched = str(td_elems[2].contents[0]).replace('\n', '').strip()
                    if (file_1 is not None) and (file_2 is not None):
                        if (file_1.find("sc_file.java") != -1) or (file_2.find("sc_file.java") != -1):
                            if file_1.find("sc_file.java") != -1:
                                start = file_2.find("(") + 1
                                percentage = int(file_2[start:].replace('%)', '').strip())/100
                            elif file_2.find("sc_file.java") != -1:
                                start = file_1.find("(") + 1
                                percentage = int(file_1[start:].replace('%)', '').strip())/100
                            rows.append({basic_keys[0]: file_1,
                                         basic_keys[1]: file_2,
                                         basic_keys[2]: lines_matched,
                                         basic_keys[3]: percentage})
    print("\t{0}% [{1}] {2}/{3} reports parsed"
          .format("100", '#' * bar_len, total, total))
    if len(join_file) == 0:
        print("Writing parsed data into file {0}...".format(report_csv_file))
        with open(report_csv_file, mode='w', encoding='utf-8', newline='') as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=basic_keys)

            csv_writer.writeheader()
            csv_writer.writerows(rows)
    else:
        print("Joining parsed data with file {0} and writing the result into file {1}..."
              .format(join_file, report_csv_file))
        to_be_joined = []
        with open(join_file, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                to_be_joined.append(row)
        joined_keys = ["SC_Filepath", "Stackoverflow_Links"]
        for key in basic_keys:
            joined_keys.append(key)
        joined_csv = []
        for csv_row in to_be_joined:
            joined_row = {}
            for key in joined_keys:
                joined_row[key] = None
            og_sc_filepath = csv_row[joined_keys[0]].strip().replace(' ', '_')
            sc_filepath_splitted = og_sc_filepath[:og_sc_filepath.find(".java")].split(os.sep)
            sc_filepath = "/".join(sc_filepath_splitted)
            og_so_link = csv_row[joined_keys[1]]
            so_link = og_so_link.split('/')
            so_identifier = None
            for i in range(len(so_link) - 1):
                if so_link[i] == "answer" or so_link[i] == "a":
                    so_identifier = "a{0}".format(int(so_link[i + 1]))
                    break
                elif so_link[i] == "questions" or so_link[i] == "q":
                    so_identifier = "q{0}".format(int(so_link[i + 1]))
                    break
            if so_identifier is not None:
                for report_row in rows:
                    file_1 = "/".join(report_row[basic_keys[0]].split(os.sep))
                    file_2 = "/".join(report_row[basic_keys[1]].split(os.sep))
                    if file_1.find(sc_filepath) != -1:
                        if file_2.find(so_identifier) != -1:
                            joined_row[joined_keys[0]] = og_sc_filepath
                            joined_row[joined_keys[1]] = og_so_link
                            joined_row[joined_keys[2]] = file_1
                            joined_row[joined_keys[3]] = file_2
                            joined_row[joined_keys[4]] = report_row[basic_keys[2]]
                            joined_row[joined_keys[5]] = report_row[basic_keys[3]]
                            break
            if joined_row[joined_keys[0]] is None:
                joined_row[joined_keys[0]] = og_sc_filepath
                joined_row[joined_keys[1]] = og_so_link
                joined_row[joined_keys[2]] = "None"
                joined_row[joined_keys[3]] = "None"
                joined_row[joined_keys[4]] = 0
                joined_row[joined_keys[5]] = 0.0
            joined_csv.append(joined_row)

        with open(report_csv_file, mode='w', encoding='utf-8', newline='') as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=joined_keys)
            csv_writer.writeheader()
            csv_writer.writerows(joined_csv)


def handle_input(user_id, base_folder, parse, only_parse, join_file):
    global report_links_file
    global report_csv_file
    if len(join_file) > 0:
        expected_keys = ["SC_Filepath", "Stackoverflow_Links"]
        with open(join_file, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            actual_keys = csv_reader.fieldnames
            if expected_keys[0] != actual_keys[0] or expected_keys[1] != actual_keys[1]:
                print("Error: Unexpected Headers! SC_Filepath and Stackoverflow_Links are required!")
                return -1
    if not only_parse:
        # get the repo folders
        sub_folders = os.listdir(base_folder)
        urls = []
        local_paths = {}
        no_resp = []
        for sub_folder in sub_folders:
            curr_dir = os.path.join(base_folder, sub_folder)
            if os.path.isdir(curr_dir):

                # get the SC and SO code folders
                sub_sub_folders = os.listdir(curr_dir)
                total = len(sub_sub_folders)
                bar_len = 50
                print("{0} has {1} folders to submit.".format(curr_dir, total))
                print("Waiting 5 Seconds before going through the folder...", end='\r')
                time.sleep(5)
                for count, sub_sub_folder in enumerate(sub_sub_folders):
                    curr_dir = os.path.join(base_folder, sub_folder, sub_sub_folder)

                    prog = int(((count + 1) * bar_len) // total)
                    bar = '#' * prog + '.' * (bar_len - prog)
                    print("\t{0}% [{1}] submitting folder {2}/{3}"
                          .format(int((prog / bar_len) * 100), bar, count + 1, total),
                          end='\r')

                    if os.path.isdir(curr_dir):
                        m = mosspy.Moss(user_id, "java")

                        # Adds all java files in the current directory as well as its subdirectories
                        wildcard = os.path.join(curr_dir, "*.java")
                        wildcard_in_sub = os.path.join(curr_dir, "*", "*.java")
                        m.addFilesByWildcard(wildcard)
                        m.addFilesByWildcard(wildcard_in_sub)

                        # Send files
                        try:
                            url = m.send()
                        except ConnectionError as e:
                            print("\r\nConnectionError: {0}!".format(e))
                            print("Trying again in 60 seconds!", end='\r')
                            time.sleep(60)
                            url = m.send()
                        except TimeoutError as e:
                            print("\r\nTimeoutError: {0}!".format(e))
                            print("Trying again in 60 seconds!", end='\r')
                            time.sleep(60)
                            url = m.send()
                        if len(url) > 0:
                            urls.append(url)
                            local_paths[url] = curr_dir
                        else:
                            no_resp.append(curr_dir)
                        time.sleep(.1)
                print("\t{0}% [{1}] {2}/{3} folders submitted"
                      .format("100", '#' * bar_len, total, total))

        report_index = ["<html><head><title>Report Index</title></head>\n\t<body><h1>Report Index</h1><br>"]
        total = len(urls)
        bar_len = 50
        if len(no_resp) > 0:
            print("Got no report for {0} submissions:".format(len(no_resp)))
            for item in no_resp:
                print("\t{0}".format(item))
        print("Finished submitting, waiting 5 Seconds before downloading the {0} reports...".format(total), end='\r')
        time.sleep(5)
        print("\nStarting download of the {0} reports...".format(total))
        for count, url in enumerate(urls):
            curr_dir = local_paths[url]

            prog = int(((count + 1) * bar_len) // total)
            bar = '#' * prog + '.' * (bar_len - prog)
            print("\t{0}% [{1}] downloading report {2}/{3}".format(int((prog / bar_len) * 100), bar, count + 1, total),
                  end='\r')

            # Download whole report locally including code diff links
            dl_report(url, os.path.join(curr_dir, "report"), max_connections=16)
            report_index.append("\t<a href=\"{0}\">{0}</a><br>".format(
                os.path.join(curr_dir, "report", "index.html")))
            time.sleep(.1)
        print("\t{0}% [{1}] {2}/{3} reports downloaded".format("100", '#' * bar_len, total, total))

        # save links to the reports in one file
        report_index.append("</body></html>")
        print("Creating report linking file {0}...".format(report_links_file))
        with open(report_links_file, mode='w', encoding='utf-8') as ofile:
            for line in report_index:
                ofile.write("{0}\n".format(line))
    if parse or only_parse:
        print("Parsing the moss reports...")
        parse_moss_reports(join_file)


parser = argparse.ArgumentParser(
    description="MOSS CLI client for submitting java files to the service and downloading the report from the service "
                "locally. Will go through the sub folders of the given folder and submit the java files for plagiarism "
                "checks and download the reports locally, creating a linking file in the process")
parser.add_argument('user_id', metavar='U', nargs=1, help="Your user-id for the MOSS service.")
parser.add_argument('folder', metavar='F', nargs=1, help="The folder whose contents you want to submit.")
parser.add_argument('-p', '--parse', action='store_true', help="Parses the moss reports into a csv file.")
parser.add_argument('-o', '--only-parse', action='store_true', help="Only parses the local moss reports and does not "
                                                                    "submit files and download the reports. Requires "
                                                                    "the reports and the links_to_reports html file "
                                                                    "created normally by this app.")
parser.add_argument('-j', '--join-file', nargs=1, default=[""], help="When the parse or only-parse option is given, "
                                                                     "joins the parsed data with the parsed data.")
args = parser.parse_args()
handle_input(args.user_id[0], args.folder[0], args.parse, args.only_parse, args.join_file[0])
