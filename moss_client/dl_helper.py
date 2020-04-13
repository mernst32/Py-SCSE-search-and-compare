from urllib.error import URLError
from urllib.request import urlopen
import os
import time
import threading
import queue
from bs4 import BeautifulSoup

lock = threading.Lock()


def dl_worker(q, base_url, dest_path, traversed):
    """
    A download worker for the moss report

    :param q: the queue, containing the links to the moss_reports parts
    :param base_url: the base_url of the moss report
    :param dest_path: where the html files should be saved to
    :param traversed: which links were already traversed
    """
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
    """
    Download a moss report and save it in the dest_path

    :param report_url: the url to the moss report
    :param dest_path: where to save the html files
    :param max_connections: how many simultaneous connections should be used at maximum
    """
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
        print("Trying again now!" + (' ' * 10), end='\r')
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
