import os

import stackexchange
import argparse
from itertools import cycle
import sys
import time
import threading
from download_stackoverflow_codesnippets.core import get_snippets_from_one_so_entity, handle_csv, get_as_snippets, \
    get_qs_snippets

done = False
data_folder = 'data'


def animate():
    loading = cycle(['|', '/', '-', '\\'])
    for c in loading:
        if done:
            break
        sys.stdout.write("\rDownloading... {0}".format(c))
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r")


def handle_input(e_id, question, best, accepted, input_file, output_file, verbose=False):
    global done
    global data_folder
    dirname = os.path.dirname(__file__)
    root_data_folder = os.path.join(dirname, data_folder)
    if not os.path.exists(root_data_folder):
        os.makedirs(root_data_folder)
    out_folder = os.path.join(dirname, data_folder, 'extracted_data')
    try:
        if not input_file:
            so = stackexchange.Site(stackexchange.StackOverflow, impose_throttling=True)
            so.app_key = "SUMnKKZdqXNa64OXduEySg(("
            so.include_body = True
            so.be_inclusive()

            result = get_snippets_from_one_so_entity(so, e_id, question, best, accepted, output_file, verbose)
            if result == 0:
                print("Done! {0} of today's API request quota used and {1} of the quota remain!"
                      .format(so.requests_used, so.requests_left))
        else:
            so_data = handle_csv(e_id, out_folder, verbose)
            if so_data == 1:
                print("The csv file needs to have the headers Stackoverflow_Links and SC_Filepath!")
                return -1
            if so_data == 2:
                print("The csv file contains invalid Stackoverflow links! Please fix them and try again.")
                return -1
            if verbose:
                print("Downloading the code snippets...")
            else:
                print("Starting download of code snippets...")
                t = threading.Thread(target=animate)
                t.daemon = True
                t.start()
            so = stackexchange.Site(stackexchange.StackOverflow, impose_throttling=True)
            so.app_key = "SUMnKKZdqXNa64OXduEySg(("
            so.include_body = True
            as_stats = get_as_snippets(so, so_data, verbose)
            qs_stats = get_qs_snippets(so, so_data, accepted, best, verbose)

            downloaded = as_stats["downloaded"] + qs_stats["downloaded"]
            saved = as_stats["saved"] + qs_stats["saved"]
            no_snippets = as_stats["no_snippets"] + qs_stats["no_snippets"]

            if verbose:
                print("Downloaded {0} code snippets from {1} Stackoverflow entries,\n"
                      "but there were {2} entities with no code snippets in their\nbody.\n"
                      .format(saved, downloaded, no_snippets))
            else:
                done = True
                time.sleep(1)
                print("Downloaded {0} code snippets from {1} Stackoverflow entries,\n"
                      "but there were {2} entities with no code snippets in their\nbody.\n"
                      .format(saved, downloaded, no_snippets))
            print("Done! {0} of today's API request quota used and {1} of the quota remain!"
                  .format(so.requests_used, so.requests_left))
    except stackexchange.StackExchangeError as e:
        done = True
        time.sleep(1)
        print("StackExchangeError: {0}".format(e.message))


parser = argparse.ArgumentParser(
    description='Download code snippets from StackOverflow')
parser.add_argument('entity_id', metavar='I', nargs=1,
                    help="The id of the entity, either an answer or a question, from which the code snippet(s) will "
                         "be downloaded.")
parser.add_argument('-q', '--question', action='store_true',
                    help="Get the code snippet(s) from a question body instead.")
parser.add_argument('-b', '--best-answer', action='store_true',
                    help="When the question option is used, this option tells the program to get the highest rated "
                         "answer of the specified question.")
parser.add_argument('-a', '--accepted-answer', action='store_true',
                    help="When the question option is used, this option tells the program to get the accepted answer "
                         "of the specified question. If there is no accepted answer the highest rated answer is used "
                         "instead. ")
parser.add_argument('-o', '--output-file', nargs=1, default=[""],
                    help="Saves extracted code snippet to file with the specified name, or if there are more than one "
                         "to a folder of the same name.")
parser.add_argument('-i', '--input-file', action='store_true',
                    help="Parses data from CSV file and uses that data to get code snippets and downloads them into "
                         "data/extracted_data/. REQUIRED HEADERS: Stackoverflow_Links, SC_Filepath. OPTIONAL HEADER: "
                         "Download.")
parser.add_argument('-v', '--verbose', action='store_true', help="gives a more detailed output")

args = parser.parse_args()
handle_input(args.entity_id[0], args.question, args.best_answer, args.accepted_answer, args.input_file,
             args.output_file[0], args.verbose)
