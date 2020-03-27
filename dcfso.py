import stackexchange
import argparse


def extract_snippets(body):
    body = body.split('\n')
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
    max = answers[0]
    for answer in answers[1:]:
        if max.score < answer.score:
            max = answer
    return max


def handle_input(e_id, question, best, accepted):
    so = stackexchange.Site(stackexchange.StackOverflow)
    so.include_body = True
    snippets = []
    if question:
        q = so.question(e_id)
        if accepted:
            a = get_accepted_answer(q)
            if a is None:
                a = get_best_answer(q)
            snippets = extract_snippets(a.body)
        if best:
            a = get_best_answer(q)
            snippets = extract_snippets(a.body)
        if not accepted and not best:
            snippets = extract_snippets(q.body)
    else:
        a = so.answer(e_id)
        snippets = extract_snippets(a.body)
    print(snippets)


parser = argparse.ArgumentParser(
    description='Download code snippets from StackOverflow')
parser.add_argument('entity_id', metavar='I', nargs=1,
                    help="The id of the entity, either an answer or a question, from which the code snippet(s) will "
                         "be downloaded.")
parser.add_argument('-q', '--question', action='store_true',
                    help="Get the code snippet(s) from a question body instead.")
parser.add_argument('-b', '--best-answer', action='store_true',
                    help="When the question option is used, this option tells the programm to get the highest rated "
                         "answer of the specified question.")
parser.add_argument('-a', '--accepted-answer', action='store_true',
                    help="When the question option is used, this option tells the program to get the accepted answer "
                         "of the specified question. If there is no accepted answer the highest rated answer is used "
                         "instead. ")

args = parser.parse_args()
handle_input(args.entity_id[0], args.question, args.best_answer, args.accepted_answer)
