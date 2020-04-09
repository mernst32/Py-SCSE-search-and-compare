import stackexchange
import argparse
from xml.sax.saxutils import unescape
import os
import csv
from shutil import copyfile
from itertools import cycle
import sys
import time
import threading

done = False


def animate():
    loading = cycle(['|', '/', '-', '\\'])
    for c in loading:
        if done:
            break
        sys.stdout.write("\rDownloading... {0}".format(c))
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r")


class StackOverflowItem:
    def __init__(self, so_id, i_type, src, dest):
        self.so_id = so_id
        self.i_type = i_type
        self.src = src
        self.dest = dest

    def print_obj(self):
        print("Obj@StackOverflowItem: [so_id={0}, i_type={1}, src={2}, dest={3}]"
              .format(self.so_id, self.i_type, self.src, self.dest))


def extract_snippets(body):
    body = unescape(body).split('\n')
    snippets = []
    snippet = []
    begin = "<pre><code>"
    end = "</code></pre>"
    is_code = False
    for line in body:
        if is_code:
            i = line.find(end)
            if i is not -1:
                is_code = False
                snippet.append(line[:i])
                snippet = "\n".join(snippet)
                snippets.append(snippet)
                snippet = []
            else:
                snippet.append(line)
        else:
            i = line.find(begin)
            if i is not -1:
                is_code = True
                snippet.append(line[(i + len(begin)):])
    return snippets


def get_accepted_answer(question):
    answers = question.answers
    for a in answers:
        if a.accepted:
            return a
    return None


def get_best_answer(question):
    answers = question.answers
    if len(answers) > 0:
        best = answers[0]
        if len(answers) > 1:
            for answer in answers[1:]:
                if best.score < answer.score:
                    best = answer
        return best
    return None


def get_all_answers(question):
    answers = question.answers
    if len(answers) > 0:
        return answers
    else:
        return None


def save_snippet_to_file(snippet, output_file, verbose=False):
    if verbose:
        print(output_file)
    with open(output_file, 'w', encoding='utf-8') as ofile:
        ofile.writelines(snippet)


def save_snippets(snippets, output_file, filename="snippet", e_id=-1, verbose=False):
    if len(snippets) >= 1:
        folder = output_file.split('.')[0]
        os.makedirs(folder, exist_ok=True)
        i = 1
        for snippet in snippets:
            save_snippet_to_file(snippet, os.path.join(folder, "{0}_{1}.java".format(filename, i)), verbose)
            i = i + 1
        return 0
    else:
        return e_id


def remove_dupl(a_list):
    return list(dict.fromkeys(a_list))


def handle_csv(input_file, verbose=False):
    so_key = "Stackoverflow_Links"
    dl_key = "Download"
    fp_key = "SC_Filepath"
    so_flag = False
    dl_flag = False
    fp_flag = False
    line_count = 0
    so_data = {"answers": [], "questions": []}
    with open(input_file, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if line_count == 0:
                for key in row:
                    if key == so_key:
                        so_flag = True
                    if key == dl_key:
                        dl_flag = True
                    if key == fp_key:
                        fp_flag = True
                line_count = line_count + 1
                if not so_flag:
                    return None
                if not fp_flag:
                    return None
            if dl_flag:
                if row[dl_key] != "TRUE":
                    line_count = line_count + 1
                    continue
            so_link = row[so_key].split('/')
            so_item = {"type": ""}
            try:
                for i in range(len(so_link) - 1):
                    if (so_link[i] == "answer") or (so_link[i] == "a"):
                        link_id = int(so_link[i + 1])
                        so_item["so_id"] = link_id
                        so_item["type"] = "a"
                        break
                    if (so_link[i] == "questions") or (so_link[i] == "q"):
                        if (i + 3) <= (len(so_link) - 1):
                            if len(so_link[i + 3]) > 0:
                                link_id = int(so_link[i + 3].split('#')[0])
                                so_item["so_id"] = link_id
                                so_item["type"] = "a"
                                break
                        else:
                            link_id = int(so_link[i + 1])
                            so_item["so_id"] = link_id
                            so_item["type"] = "q"
                            break
                so_item["src"] = row[fp_key]
                so_item["dest"] = os.path.join(input_file.split('.')[0], row[fp_key].split('.')[0], "sc_file.java")
            except ValueError:
                print("On line {0}: the SO link \"{1}\" is invalid!".format(line_count + 1, row[so_key]))
            if so_item["type"] == "a":
                found = False
                for elem in so_data["answers"]:
                    if elem.so_id == so_item["so_id"]:
                        elem.src.append(so_item["src"])
                        elem.dest.append(so_item["dest"])
                        found = True
                        break
                if not found:
                    so_data["answers"].append(StackOverflowItem(so_item["so_id"], so_item["type"],
                                                                [so_item["src"]], [so_item["dest"]]))
            if so_item["type"] == "q":
                found = False
                for elem in so_data["answers"]:
                    if elem.so_id == so_item["so_id"]:
                        elem.src.append(so_item["src"])
                        elem.dest.append(so_item["dest"])
                        found = True
                        break
                if not found:
                    so_data["questions"].append(StackOverflowItem(so_item["so_id"], so_item["type"],
                                                                  [so_item["src"]], [so_item["dest"]]))
            line_count = line_count + 1
    print("Processed {0} line(s).".format(line_count))
    print("Got {0} ids comprised of {1} answer-ids and {2} question-ids.\n"
          .format((len(so_data["answers"]) + len(so_data["questions"])),
                  len(so_data["answers"]), len(so_data["questions"])))
    return so_data


def chunks(a_list, n):
    for i in range(0, len(a_list), n):
        yield a_list[i:i + n]


def save_as_snippets(snippets, so_items, nid, direct_link=True, aid=-1, verbose=False, copy=True):
    downloaded = 0
    saved = 0
    no_snippets = 0
    if len(snippets) > 0:
        downloaded = 1
        for so_item in so_items:
            if nid == so_item.so_id:
                for dest in so_item.dest:
                    for src in so_item.src:
                        if copy:
                            try:
                                copyfile(src, dest)
                            except FileNotFoundError:
                                os.makedirs(os.path.dirname(dest), exist_ok=True)
                                copyfile(src, dest)
                            if verbose:
                                print("cp: {0} -> {1}".format(src, dest))
                    if direct_link:
                        path = os.path.join(os.path.dirname(dest), "a{0}.java".format(nid))
                        filename = "snippet"
                    else:
                        path = os.path.join(os.path.dirname(dest), "a_from_q{0}.java".format(nid))
                        filename = "a{0}".format(aid)
                    res = save_snippets(snippets,
                                        path,
                                        filename=filename, verbose=verbose)
                    if res == 0:
                        saved = saved + len(snippets)
    else:
        no_snippets = 1
    return {"downloaded": downloaded, "saved": saved, "no_snippets": no_snippets}


def save_qs_snippets(snippets, so_items, nid, verbose=False, copy=True):
    downloaded = 0
    saved = 0
    no_snippets = 0
    if len(snippets) > 0:
        downloaded = 1
        for so_item in so_items:
            if nid == so_item.so_id:
                for dest in so_item.dest:
                    for src in so_item.src:
                        if copy:
                            try:
                                copyfile(src, dest)
                            except FileNotFoundError:
                                os.makedirs(os.path.dirname(dest), exist_ok=True)
                                copyfile(src, dest)
                            if verbose:
                                print("cp: {0} -> {1}".format(src, dest))
                    res = save_snippets(snippets,
                                        os.path.join(os.path.dirname(dest), "q{0}.java".format(nid)),
                                        verbose=verbose)
                    if res == 0:
                        saved = saved + len(snippets)
    else:
        no_snippets = 1
    return {"downloaded": downloaded, "saved": saved, "no_snippets": no_snippets}


def get_as_snippets(so, so_data, verbose=False):
    downloaded = 0
    saved = 0
    no_snippets = 0
    for count, chunk in enumerate(list(chunks(so_data["answers"], 100))):
        if count % 20:
            time.sleep(1)
        a_ids = []
        for so_item in chunk:
            a_ids.append(so_item.so_id)
        answers = so.answers(a_ids, pagesize=100)
        for a in answers:
            snippets = extract_snippets(a.body)
            result = save_as_snippets(snippets, chunk, a.id, verbose)
            downloaded = downloaded + result["downloaded"]
            saved = saved + result["saved"]
            no_snippets = no_snippets + result["no_snippets"]
    return {"downloaded": downloaded, "saved": saved, "no_snippets": no_snippets}


def get_qs_snippets(so, so_data, accepted=False, best=False, verbose=False):
    downloaded = 0
    saved = 0
    no_snippets = 0
    for count, chunk in enumerate(list(chunks(so_data["questions"], 100))):
        if count % 20:
            time.sleep(1)
        q_ids = []
        for so_item in chunk:
            q_ids.append(so_item.so_id)
        questions = so.questions(q_ids, pagesize=100)
        for q in questions:
            if accepted or best:
                a = None
                if accepted:
                    a = get_accepted_answer(q)
                if a is None:
                    a = get_best_answer(q)
                if a is not None:
                    snippets = extract_snippets(a.body)
                    result = save_as_snippets(snippets, chunk, q.id, direct_link=False, verbose=verbose)
                    downloaded = downloaded + result["downloaded"]
                    saved = saved + result["saved"]
                    no_snippets = no_snippets + result["no_snippets"]
            else:
                snippets = extract_snippets(q.body)
                result = save_qs_snippets(snippets, chunk, q.id, verbose)
                downloaded = downloaded + result["downloaded"]
                saved = saved + result["saved"]
                no_snippets = no_snippets + result["no_snippets"]

                answers = get_all_answers(q)
                if answers is not None:
                    for a in answers:
                        snippets = extract_snippets(a.body)
                        result = save_as_snippets(snippets, chunk, q.id, direct_link=False, verbose=verbose,
                                                  aid=a.id)
                        downloaded = downloaded + result["downloaded"]
                        saved = saved + result["saved"]
                        no_snippets = no_snippets + result["no_snippets"]
    return {"downloaded": downloaded, "saved": saved, "no_snippets": no_snippets}


def get_snippets_from_one_so_entity(so, e_id, question, best, accepted, output_file, verbose=False):
    snippets = []
    try:
        e_id = int(e_id)
        if question:
            q = so.question(e_id)
            if accepted:
                a = get_accepted_answer(q)
                if a is None:
                    a = get_best_answer(q)
                if a is None:
                    print("Question {0} has no answers!".format(e_id))
                    return -1
                print("Extract code snippets from answer {0}...".format(e_id))
                snippets = extract_snippets(a.body)
            if best:
                a = get_best_answer(q)
                if a is None:
                    print("Question {0} has no answers!".format(e_id))
                    return -1
                print("Extract code snippets from answer {0}...".format(e_id))
                snippets = extract_snippets(a.body)
            if not accepted and not best:
                print("Extract code snippets from question {0}...".format(e_id))
                snippets = extract_snippets(q.body)
        else:
            a = so.answer(e_id)
            print("Extract code snippets from answer {0}...".format(e_id))
            snippets = extract_snippets(a.body)
        if len(output_file) == 0:
            if len(snippets) == 0:
                print("{0}: No code snippets to download!".format(e_id))
            else:
                i = 1
                for snippet in snippets:
                    print(("=" * 25) + ("[ {0}. Snippet ]".format(i)) + ("=" * 25))
                    print(snippet)
                    i = i + 1
        else:
            res = save_snippets(snippets, output_file, e_id=e_id, verbose=verbose)
            if res is not 0:
                print("{0} had no code snippet in its body!".format(res))
            elif res is -1:
                print("Found no code snippet in the body!")
    except ValueError as e:
        print("ValueError: Please use an integer for I, was \'{0}\'".format(e_id))
        return -1
    return 0


def handle_input(e_id, question, best, accepted, input_file, output_file, verbose=False):
    global done
    so = stackexchange.Site(stackexchange.StackOverflow, impose_throttling=True)
    so.app_key = "SUMnKKZdqXNa64OXduEySg(("
    so.include_body = True
    try:
        if not input_file:
            result = get_snippets_from_one_so_entity(so, e_id, question, best, accepted, output_file, verbose)
            if result == 0:
                print("Done! {0} of today's API request quota used and {1} of the quota remain!"
                      .format(so.requests_used, so.requests_left))
        else:
            so_data = handle_csv(e_id, verbose)
            if so_data is None:
                print("The csv file needs to have the headers Stackoverflow_Links and SC_Filepath!")
                return -1
            if verbose:
                print("Downloading the code snippets...")
            else:
                print("Starting download of code snippets...")
                t = threading.Thread(target=animate)
                t.daemon = True
                t.start()
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
                    help="Parses data from CSV file and uses them to get code snippets. REQUIRED HEADERS: "
                         "Stackoverflow_Links, SC_Filepath. OPTIONAL HEADER: Download.")
parser.add_argument('-v', '--verbose', action='store_true', help="gives a more detailed output")

args = parser.parse_args()
handle_input(args.entity_id[0], args.question, args.best_answer, args.accepted_answer, args.input_file,
             args.output_file[0], args.verbose)
