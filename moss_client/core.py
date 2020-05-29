import csv
import mosspy
import os
import time
from bs4 import BeautifulSoup

from moss_client.dl_helper import dl_report
known_repos = ['Bitbucket', 'GitLab', 'Github', 'Gitorious', 'Google_Code', 'Fedora_Project', 'Google_Android']


def parse_reports_into_dict(paths, src_repo):
    """
    Parses moss reports into dictionary list

    :param paths: a list of paths pointing to the moss reports
    :param src_repo: a dict of the repo where the test files come from, using the paths as key
    :return:  a dict list containing the parsed data from reports to the sc_file(the file to be tested)
    """
    total = len(paths)
    bar_len = 50
    rows = []
    basic_keys = ['File_1', 'File_2', 'Lines_Matched', 'Code_Similarity', 'Src_Repo']
    print("Following the gathered paths to the reports and parsing those...")
    for count, link in enumerate(paths):

        repo_name = src_repo[link]
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
                                percentage = int(file_2[start:].replace('%)', '').strip()) / 100
                            elif file_2.find("sc_file.java") != -1:
                                start = file_1.find("(") + 1
                                percentage = int(file_1[start:].replace('%)', '').strip()) / 100
                            rows.append({basic_keys[0]: file_1,
                                         basic_keys[1]: file_2,
                                         basic_keys[2]: lines_matched,
                                         basic_keys[3]: percentage,
                                         basic_keys[4]: repo_name})
    print("\t{0}% [{1}] {2}/{3} reports parsed"
          .format("100", '#' * bar_len, total, total))
    return rows


def join_parsed_data_with(parsed_data, join_file, report_csv_file):
    """
    Joins the parsed_data from the moss_reports with the given join_file and saves it into the report_csv_file
    :param parsed_data: a dict list containing the parsed data from reports to the sc_file(the file to be tested)
    :param join_file: the name of the csv file to be joined
    :param report_csv_file: the name of the file into which the joined data will be saved
    """
    if len(parsed_data) > 0:
        basic_keys = list(parsed_data[0].keys())
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
                for parsed_row in parsed_data:
                    file_1 = "/".join(parsed_row[basic_keys[0]].split(os.sep))
                    file_2 = "/".join(parsed_row[basic_keys[1]].split(os.sep))
                    if file_1.find(sc_filepath) != -1:
                        if file_2.find(so_identifier) != -1:
                            joined_row[joined_keys[0]] = og_sc_filepath
                            joined_row[joined_keys[1]] = og_so_link
                            joined_row[joined_keys[2]] = file_1
                            joined_row[joined_keys[3]] = file_2
                            joined_row[joined_keys[4]] = parsed_row[basic_keys[2]]
                            joined_row[joined_keys[5]] = parsed_row[basic_keys[3]]
                            joined_row[joined_keys[6]] = parsed_row[basic_keys[4]].replace(' ', '_')
                            break
            if joined_row[joined_keys[0]] is None:
                repo_name = "None"
                for repo in known_repos:
                    if repo in og_sc_filepath:
                        repo_name = repo

                joined_row[joined_keys[0]] = og_sc_filepath
                joined_row[joined_keys[1]] = og_so_link
                joined_row[joined_keys[2]] = "None"
                joined_row[joined_keys[3]] = "None"
                joined_row[joined_keys[4]] = 0
                joined_row[joined_keys[5]] = 0.0
                joined_row[joined_keys[6]] = repo_name
            joined_csv.append(joined_row)

        with open(report_csv_file, mode='w', encoding='utf-8', newline='') as csv_file:
            csv_writer = csv.DictWriter(csv_file, fieldnames=joined_keys)
            csv_writer.writeheader()
            csv_writer.writerows(joined_csv)


def parse_moss_reports(report_links_file, report_csv_file, join_file):
    """
    Parses the links to the moss reports master file for the paths to the moss reports. Then parses the moss_reports
    and saves them into the report_csv_file.

    :param report_links_file: the name of the moss reports master file containing the paths
    :param report_csv_file: the output file
    :param join_file: the file to join with the resulting data
    """
    links = []
    src_repo = {}
    print("Getting paths to reports from file {0}...".format(report_links_file))
    with open(report_links_file, mode='r', encoding='utf-8') as html:
        soup = BeautifulSoup(html, 'lxml')
        a_elems = soup.find_all('a')
        for a_elem in a_elems:
            if a_elem.has_attr('href'):
                path = a_elem["href"]
                src_repo[path] = str(a_elem.contents[0]).split('from')[1].strip()
                links.append(path)

    parsed_data = parse_reports_into_dict(links, src_repo)

    if len(parsed_data) > 0:
        basic_keys = list(parsed_data[0].keys())
        if len(join_file) == 0:
            print("Writing parsed data into file {0}...".format(report_csv_file))
            with open(report_csv_file, mode='w', encoding='utf-8', newline='') as csv_file:
                csv_writer = csv.DictWriter(csv_file, fieldnames=basic_keys)

                csv_writer.writeheader()
                csv_writer.writerows(parsed_data)
        else:
            join_parsed_data_with(parsed_data, join_file, report_csv_file)


def submit_files(user_id, base_folder, batch):
    """
    Submits the java files in the base_folder to moss.stanford.edu for comparison

    :param user_id: the user_id for the moss service
    :param base_folder: the folder whose java files need to tested
    :param batch: whether the submitting should be done in batches of only 100, also ignores already submitted folders
    :return: a triple (urls, local_path, src_repo). urls is a list of links pointing to the moss reports and local_path
        is a dict using urls as key and contains the local_path to the submitted folders. Whereas src_repo is a dict
        containing the names of the repositories from where the files comes from.
    """
    # get the repo folders

    sub_folders = os.listdir(base_folder)
    urls = []
    local_paths = {}
    src_repo = {}
    no_resp = []
    total_submitted = 0
    already_submitted = 0
    for sub_folder in sub_folders:
        curr_dir = os.path.join(base_folder, sub_folder)
        if os.path.isdir(curr_dir):

            # get the SC and SO code folders
            sub_sub_folders = os.listdir(curr_dir)
            total = len(sub_sub_folders)
            bar_len = 50
            repo = os.path.basename(curr_dir)
            print("{0} has {1} folders to submit.".format(repo, total))
            print("Waiting 5 Seconds before going through the folder...", end='\r')
            time.sleep(5)
            for count, sub_sub_folder in enumerate(sub_sub_folders):
                curr_dir = os.path.join(base_folder, sub_folder, sub_sub_folder)

                prog = int(((count + 1) * bar_len) // total)
                bar = '#' * prog + '.' * (bar_len - prog)
                print("\t{0}% [{1}] parsing folder {2}/{3}"
                      .format(int((prog / bar_len) * 100), bar, count + 1, total),
                      end='\r')

                if os.path.isdir(curr_dir):
                    if "report" in os.listdir(curr_dir):
                        url = "local_{0}".format(already_submitted)
                        urls.append(url)
                        local_paths[url] = curr_dir
                        src_repo[url] = repo
                        already_submitted = already_submitted + 1
                        continue
                    if batch:
                        if total_submitted >= 100:
                            print("WARN: Batching limit reached! Won't download more!")
                            break
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
                        print("Trying again now!" + (' ' * 10), end='\r')
                        url = m.send()
                    except TimeoutError as e:
                        print("\r\nTimeoutError: {0}!".format(e))
                        print("Trying again in 60 seconds!", end='\r')
                        time.sleep(60)
                        print("Trying again now!" + (' ' * 10), end='\r')
                        url = m.send()
                    if len(url) > 0:
                        urls.append(url)
                        local_paths[url] = curr_dir
                        src_repo[url] = repo
                    else:
                        no_resp.append(curr_dir)
                    time.sleep(.1)
                    total_submitted = total_submitted + 1
            print("\t{0}% [{1}] {2}/{3} folders have been parsed"
                  .format("100", '#' * bar_len, total, total))
    if len(no_resp) > 0:
        print("Got no report for {0} submissions:".format(len(no_resp)))
        for item in no_resp:
            print("\t{0}".format(item))
    print("Submitted {0} folders!".format(total_submitted))
    print("{0} folders have already been submitted!".format(already_submitted))
    return urls, local_paths, src_repo


def submit_and_dl(user_id, base_folder, report_links_file, batch):
    """
    Submit the java file in the base_folder and download the reports. Afterwards create a html file with the locallinks
    to the reports.
    :param user_id: the user_id for the moss_service
    :param base_folder: the folder whose java files will be submitted
    :param report_links_file: the name of the html file containing the local links to the moss reports
    :param batch: whether the submitting should be done in batches of only 100, also ignores already submitted folders
    """
    urls, local_paths, src_repo = submit_files(user_id, base_folder, batch)

    report_index = ["<html><head><title>Report Index</title></head>\n\t<body><h1>Report Index</h1><br>"]
    total = len(urls)
    bar_len = 50
    print("Finished submitting, waiting 5 Seconds before parsing the {0} reports...".format(total), end='\r')
    time.sleep(5)
    print("\nStarting download/parsing of the {0} reports...".format(total))
    for count, url in enumerate(urls):
        curr_dir = local_paths[url]
        repo = src_repo[url]

        prog = int(((count + 1) * bar_len) // total)
        bar = '#' * prog + '.' * (bar_len - prog)
        print("\t{0}% [{1}] downloading/parsing report {2}/{3}".format(int((prog / bar_len) * 100), bar, count + 1, total),
              end='\r')

        # Download whole report locally including code diff links
        if "local_" not in url:
            dl_report(url, os.path.join(curr_dir, "report"), max_connections=16)
        report_index.append("\t<a href=\"{0}\">{0} from {1}</a><br>"
                            .format(os.path.join(curr_dir, "report", "index.html"), repo))
        time.sleep(.1)
    print("\t{0}% [{1}] {2}/{3} reports downloaded/parsed".format("100", '#' * bar_len, total, total))

    # save links to the reports in one file
    report_index.append("</body></html>")

    print("Creating report linking file {0}...".format(report_links_file))
    with open(report_links_file, mode='w', encoding='utf-8') as ofile:
        for line in report_index:
            ofile.write("{0}\n".format(line))
