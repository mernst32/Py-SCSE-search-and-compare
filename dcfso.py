import stackexchange

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


so = stackexchange.Site(stackexchange.StackOverflow)
so.include_body = True

# https://stackoverflow.com/a/992060
a = so.answer(992060)
print(len(extract_snippets(a.body)))

