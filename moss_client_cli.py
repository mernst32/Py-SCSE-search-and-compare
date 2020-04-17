import argparse
import csv
import os
from moss_client.core import submit_and_dl, parse_moss_reports

data_folder = 'data'


def handle_input(user_id, base_folder, parse, only_parse, join_file):
    global data_folder
    abs_path = os.path.abspath(os.path.dirname(__file__))
    root_data_folder = os.path.join(abs_path, data_folder)
    if not os.path.exists(root_data_folder):
        os.makedirs(root_data_folder)
    report_links_file = os.path.join(root_data_folder, 'links_to_moss_reports.html')
    report_csv_file = os.path.join(root_data_folder, 'moss_report.csv')
    if not os.path.isabs(base_folder):
        base_folder = os.path.join(abs_path, base_folder)

    if len(join_file) > 0:
        expected_keys = ["SC_Filepath", "Stackoverflow_Links"]
        with open(join_file, mode='r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            actual_keys = csv_reader.fieldnames
            if expected_keys[0] != actual_keys[0] or expected_keys[1] != actual_keys[1]:
                print("Error: Unexpected Headers! SC_Filepath and Stackoverflow_Links are required!")
                return -1
    if not only_parse:
        submit_and_dl(user_id, base_folder, report_links_file)
    if parse or only_parse:
        print("Parsing the moss reports...")
        parse_moss_reports(report_links_file, report_csv_file, join_file)


parser = argparse.ArgumentParser(
    description="MOSS CLI client for submitting java files to the service and downloading the report from the service "
                "locally. Will go through the sub folders of the given folder and submit the java files for plagiarism "
                "checks and download the reports locally, creating a linking file in the process")
parser.add_argument('user_id', metavar='U', nargs=1, help="Your user-id for the MOSS service.")
parser.add_argument('folder', metavar='F', nargs=1, help="The folder whose contents you want to submit.")
parser.add_argument('-p', '--parse', action='store_true', help="Parses the moss reports into a csv file.")
parser.add_argument('-o', '--only-parse', action='store_true',
                    help="Only parses the local moss reports and does not submit files and download the reports. "
                         "Requires the reports and the links_to_reports html file created normally by this app.")
parser.add_argument('-j', '--join-file', nargs=1, default=[""],
                    help="When the parse or only-parse option is given, joins the parsed data with the parsed data.")
args = parser.parse_args()
handle_input(args.user_id[0], args.folder[0], args.parse, args.only_parse, args.join_file[0])
