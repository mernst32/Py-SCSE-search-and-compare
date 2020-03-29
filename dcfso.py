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


def save_snippet_to_file(snippet, output_file, verbose=False):
    if verbose:
        print(output_file)
    try:
        with open(output_file, 'w', encoding='utf-8') as ofile:
            ofile.writelines(snippet)
    except FileNotFoundError:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)


def save_snippets(snippets, output_file, filename="snippet", e_id=-1, verbose=False):
    if len(snippets) == 1:
        save_snippet_to_file(snippets, output_file, verbose)
        return 0
    elif len(snippets) > 1:
        folder = output_file.split('.')[0]
        os.makedirs(folder, exist_ok=True)
        i = 1
        for snippet in snippets:
            save_snippet_to_file(snippet, os.path.join(folder, "{0}_{1}.java".format(filename, i)), verbose)
            i = i + 1
        return 0
    else:
        return e_id


def handle_csv(input_file, verbose=False):
    so_key = "Stackoverflow_Links"
    dl_key = "Download"
    fp_key = "SC_Filepath"
    so_flag = False
    dl_flag = False
    fp_flag = False
    line_count = 0
    so_ids = {"answers": [], "questions": [], "src": {}, "dest": {}}
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
            try:
                for i in range(len(so_link) - 1):
                    if (so_link[i] == "answer") or (so_link[i] == "a"):
                        link_id = int(so_link[i + 1])
                        so_ids["answers"].append(link_id)
                        last_id = link_id
                        continue
                    if (so_link[i] == "questions") or (so_link[i] == "q"):
                        if (i + 3) <= (len(so_link) - 1):
                            if len(so_link[i + 3]) > 0:
                                link_id = int(so_link[i + 3].split('#')[0])
                                so_ids["answers"].append(link_id)
                                last_id = link_id
                                continue
                        else:
                            link_id = int(so_link[i + 1])
                            so_ids["questions"].append(link_id)
                            last_id = link_id
                            continue
                dest = os.path.join(input_file.split('.')[0], row[fp_key].split('.')[0])
            except ValueError:
                print("On line {0}: the SO link \"{1}\" is invalid!".format(line_count + 1, row[so_key]))
            so_ids["src"][last_id] = row[fp_key]
            so_ids["dest"][last_id] = dest
            line_count = line_count + 1
    print("Processed {0} line(s).".format(line_count))
    return so_ids


def chunks(a_list, n):
    for i in range(0, len(a_list), n):
        yield a_list[i:i + n]


def handle_input(e_id, question, best, accepted, input_file, output_file, verbose=False):
    global done
    so = stackexchange.Site(stackexchange.StackOverflow)
    so.include_body = True
    snippets = []
    try:
        if not input_file:
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
            except ValueError:
                print("Please enter an Integer for I!")
        else:
            no_snippets = {"answers": [], "questions": []}
            so_ids = handle_csv(e_id, verbose)
            if so_ids is None:
                print("The csv file needs to have the headers Stackoverflow_Links and SC_Filepath!")
                return -1
            print("Got {0} ids comprised of {1} answer-ids and {2} question-ids.\n"
                  .format((len(so_ids["answers"]) + len(so_ids["questions"])),
                          len(so_ids["answers"]), len(so_ids["questions"])))
            downloaded = 0
            no_answers = 0
            if verbose:
                print("Downloading the code snippets...")
            else:
                print("Starting download of code snippets...")
                t = threading.Thread(target=animate)
                t.daemon = True
                t.start()
            for chunk in list(chunks(so_ids["answers"], 100)):
                answers = so.answers(chunk, pagesize=100)
                print("a: " + str(answers.pagesize))
                for a in answers:
                    snippets = extract_snippets(a.body)
                    res = save_snippets(snippets, os.path.join(so_ids["dest"][a.id], "a_{0}.java".format(a.id)),
                                        e_id=a.id, verbose=verbose)
                    if (res is not 0) and (res is not -1):
                        no_snippets["answers"].append(res)
                    if res is 0:
                        downloaded = downloaded + 1
                        copyfile(so_ids["src"][a.id], os.path.join(so_ids["dest"][a.id], "sc_file.java"))
                        if verbose:
                            print("cp: {0} -> {1}".format(so_ids["src"][a.id], so_ids["dest"][a.id]))
            for chunk in list(chunks(so_ids["questions"], 100)):
                questions = so.questions(chunk, pagesize=100)
                print("q: " + str(questions.pagesize))
                for q in questions:
                    if accepted or best:
                        a = None
                        if accepted:
                            a = get_accepted_answer(q)
                        if a is None:
                            a = get_best_answer(q)
                        if a is None:
                            no_answers = no_answers + 1
                            if verbose:
                                print("Question {0} has no answers!".format(q.id))
                        else:
                            res = save_snippets(extract_snippets(a.body),
                                                os.path.join(so_ids["dest"][q.id], "a_{0}.java".format(q.id)),
                                                e_id=a.id, verbose=verbose)
                            if (res is not 0) and (res is not -1):
                                no_snippets["answers"].append(res)
                            if res is 0:
                                downloaded = downloaded + 1
                                copyfile(so_ids["src"][q.id], os.path.join(so_ids["dest"][q.id], "sc_file.java"))
                                if verbose:
                                    print("cp: {0} -> {1}".format(so_ids["src"][q.id], so_ids["dest"][q.id]))
                    if (not best) and (not accepted):
                        res = save_snippets(extract_snippets(q.body),
                                            os.path.join(so_ids["dest"][q.id], "q_{0}.java".format(q.id)),
                                            e_id=q.id, verbose=verbose)
                        if (res is not 0) and (res is not -1):
                            no_snippets["questions"].append(res)
                        if res is 0:
                            downloaded = downloaded + 1
                            copyfile(so_ids["src"][q.id], os.path.join(so_ids["dest"][q.id], "sc_file.java"))
                            if verbose:
                                print("cp: {0} -> {1}".format(so_ids["src"][q.id], so_ids["dest"][q.id]))
            if verbose:
                if len(no_snippets["answers"]) > 0:
                    print("The following answers had no code snippets in their body:\n{0}"
                          .format(no_snippets["answers"]))
                if len(no_snippets["questions"]) > 0:
                    print("The following questions had no code snippets in their body:\n{0}"
                          .format(no_snippets["questions"]))
                print("Downloaded code snippets from {0} Stackoverflow entries,\n"
                      "but there were {1} answers and {2} questions with no code\n"
                      "snippets in their body and {3} questions without any answers.\n"
                      .format(downloaded, len(no_snippets["answers"]), len(no_snippets["questions"]), no_answers))
            else:
                done = True
                time.sleep(1)
                print("Downloaded code snippets from {0} Stackoverflow entries,\n"
                      "but there were {1} answers and {2} questions with no code\n"
                      "snippets in their body and {3} questions without any answers.\n"
                      .format(downloaded, len(no_snippets["answers"]), len(no_snippets["questions"]), no_answers))
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
