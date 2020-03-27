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
                snippet = '\n'.join(snippet)
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


def handle_input(id):
    so = stackexchange.Site(stackexchange.StackOverflow)
    so.include_body = True
    a = so.answer(id)
    print(len(extract_snippets(a.body)))


parser = argparse.ArgumentParser(
    description='Download code snippets from StackOverflow')
parser.add_argument('entity_id', metavar='I', nargs=1, help="The id of the entity, answer is the default, from which "
                                                            "the code snippets will be downloaded.")
args = parser.parse_args()
handle_input(args.entity_id[0])
