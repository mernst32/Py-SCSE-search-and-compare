import stackexchange
import argparse
from xml.sax.saxutils import unescape
import os


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


def handle_input(e_id, question, best, accepted, input_file, output_file, verbose=False):
    so = stackexchange.Site(stackexchange.StackOverflow)
    so.include_body = True
    snippets = []
    if len(input_file) == 0:
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
parser.add_argument('-i', '--input-file', nargs=1, default=[""],
                    help="Parses data from CSV file and uses them to get code snippets. REQUIRED HEADER: "
                         "\"Stackoverflow_Links\". OPTIONAL HEADERS: \"Download\",\"SC_Filepath\".")
parser.add_argument('-v', '--verbose', action='store_true', help="gives a more detailed output")

args = parser.parse_args()
handle_input(args.entity_id[0], args.question, args.best_answer, args.accepted_answer, args.input_file[0],
             args.output_file[0], args.verbose)
