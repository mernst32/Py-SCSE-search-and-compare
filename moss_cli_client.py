import argparse
from urllib.request import urlopen
import mosspy
import os
import logging
import time
import threading
import queue
from bs4 import BeautifulSoup


lock = threading.Lock()


def dl_worker(q, base_url, dest_path, traversed):
    while True:
        url = q.get()
        if url is None:
            break
        with lock:
            traversed.append(url)
        basename = os.path.basename(url)
        response = urlopen(url)
        html = response.read()
        soup = BeautifulSoup(html, 'lxml')
        children = soup.find_all('frame')
        edges = []
        for child in children:
            if child.has_attr('src'):
                edge = child.get('src')
                if edge.find("match") != -1 and edge.find('#') == -1:
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
    response = urlopen(report_url)
    html = response.read()
    soup = BeautifulSoup(html, 'lxml')
    children = soup.find_all('a')
    edges = []
    traversed = []
    for child in children:
        if child.has_attr('href'):
            edge = child.get('href')
            if edge.find("match") != -1 and edge.find('#') == -1:
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


def handle_input(user_id, base_folder):
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
                        print("\r\nError occurred: {0}! Trying again in 60 seconds!".format(e))
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
    report_path = r'links_to_reports.html'
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
