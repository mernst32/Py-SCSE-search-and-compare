import stackexchange
import argparse
from xml.sax.saxutils import unescape
import os
import csv
from shutil import copyfile


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
    best = answers[0]
    for answer in answers[1:]:
        if best.score < answer.score:
            best = answer
    return best


def save_snippet_to_file(snippet, output_file, verbose=False):
    if verbose:
        print(output_file)
    with open(output_file, 'w', encoding='utf-8') as ofile:
        ofile.writelines(snippet)


def save_snippets(snippets, output_file, filename="snippet", e_id=-1, verbose=False):
    if len(snippets) == 1:
        save_snippet_to_file(snippets, output_file, verbose)
    elif len(snippets) > 1:
        folder = output_file.split('.')[0]
        try:
            os.makedirs(folder)
        except FileExistsError:
            pass
        i = 1
        for snippet in snippets:
            save_snippet_to_file(snippet, os.path.join(folder, "{0}_{1}.java".format(filename, i)), verbose)
            i = i + 1
    else:
        if e_id is not -1:
            print("{0}: No code snippets to download!".format(e_id))
        else:
            print("No code snippets to download!")


def handle_csv(input_file, verbose=False):
    so_key = "Stackoverflow_Links"
    dl_key = "Download"
    fp_key = "SC_Filepath"
    so_flag = False
    dl_flag = False
    fp_flag = False
    line_count = 0
    so_ids = {"answers": [], "questions": [], "dest": {}}
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
            for i in range(len(so_link) - 1):
                if (so_link[i] == "answer") or (so_link[i] == "a"):
                    link_id = so_link[i + 1]
                    so_ids["answers"].append(link_id)
                    last_id = link_id
                if (so_link[i] == "questions") or (so_link[i] == "q"):
                    if (i + 3) == (len(so_link) - 1):
                        if so_link[i + 3] != "":
                            link_id = so_link[i + 3].split('#')[0]
                            so_ids["answers"].append(link_id)
                            last_id = link_id
                    else:
                        link_id = so_link[i + 1]
                        so_ids["questions"].append(link_id)
                        last_id = link_id
            dest = os.path.join(input_file.split('.')[0], row[fp_key].split('.')[0], "searchcode_file.java")
            try:
                copyfile(row[fp_key], dest)
            except FileNotFoundError:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                copyfile(row[fp_key], dest)
            if verbose:
                print("cp {0} to {1}".format(row[fp_key], dest))
            so_ids["dest"][last_id] = os.path.dirname(dest)
            line_count = line_count + 1
    if verbose:
        print("Processed {0} line(s).".format(line_count))
    return so_ids


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def handle_input(e_id, question, best, accepted, input_file, output_file, verbose=False):
    so = stackexchange.Site(stackexchange.StackOverflow)
    so.include_body = True
    snippets = []
    if not input_file:
        try:
            e_id = int(e_id)
            if question:
                q = so.question(e_id)
                if accepted:
                    a = get_accepted_answer(q)
                    if a is None:
                        a = get_best_answer(q)
                    print("Extract code snippets from answer {0}...".format(e_id))
                    snippets = extract_snippets(a.body)
                if best:
                    a = get_best_answer(q)
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
                save_snippets(snippets, output_file, e_id=e_id, verbose=verbose)
        except ValueError:
            print("Please enter an Integer for I!")
    else:
        so_ids = handle_csv(e_id, verbose)
        print("Got {0} answer-ids and {1} question-ids".format(len(so_ids["answers"]), len(so_ids["questions"])))
        print("Downloading the code snippets...")
        for chunk in list(chunks(so_ids["answers"], 100)):
            answers = so.answers(chunk)
            for a in answers:
                snippets = extract_snippets(a.body)
                save_snippets(snippets, os.path.join(so_ids["dest"][str(a.id)], "soa_{0}.java".format(a.id)),
                              e_id=a.id, verbose=verbose)
        print(so_ids["questions"])
        for chunk in list(chunks(so_ids["questions"], 100)):
            questions = so.questions(chunk)
            for q in questions:
                n_id = 0
                if best:
                    a = get_best_answer(q)
                    snippets = extract_snippets(a.body)
                if accepted:
                    a = get_accepted_answer(q)
                    if a is None:
                        a = get_best_answer(q)
                    snippets = extract_snippets(a.body)
                if (not best) and (not accepted):
                    snippets = extract_snippets(q.body)
                    save_snippets(snippets, os.path.join(so_ids["dest"][str(q.id)], "soa_{0}.java".format(q.id)),
                                  e_id=q.id, verbose=verbose)
    print("Done!")


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
