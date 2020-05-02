from xml.sax.saxutils import unescape
import os
import csv
from shutil import copyfile
import time

from download_stackoverflow_codesnippets.so_helper import StackOverflowItem, chunks, get_accepted_answer, \
    get_best_answer, get_all_answers


def extract_snippets(body):
    """
    Extracts the code snippets from the body of a Stackoverflow Entity

    :param body: the body of stackoverflow entity
    :return: a string list containing all the snippets that were found in the body
    """
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


def save_snippet_to_file(snippet, output_file, verbose=False):
    """
    Save one code snippet into given output file.

    :param snippet: a string containing the code snippet
    :param output_file: the name of the file to which the snippet will be saved
    :param verbose: print more data
    """
    if verbose:
        print(output_file)
    with open(output_file, 'w', encoding='utf-8') as ofile:
        ofile.writelines(snippet)


def save_snippets(snippets, output_file, filename="snippet", e_id=-1, verbose=False):
    """
    Save multiple snippets

    :param snippets: a list of strings containing the snippets
    :param output_file: the folder to which the snippets will be saved
    :param filename: the filenames for the snippets
    :param e_id: the id of the stackoverflow entity whose body the snippets are from
    :param verbose: prints more data
    :return: if the saving was successful returns 0 otherwise the e_id
    """
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


def handle_csv(input_file, output_folder, verbose=False):
    """
    Parse the data of a csv for getting code snippets. The csv should at leatst have the headers Stackoverflow_Links and
    SC_Filepath.

    :param input_file: the filename of the csv
    :param output_folder: the folder to which the gotten code snippets saved in
    :param verbose: print more data
    :return: a dict list containing the stackoverflow items gotten from the csv.
    """
    so_key = "Stackoverflow_Links"
    dl_key = "Download"
    fp_key = "SC_Filepath"
    so_flag = False
    dl_flag = False
    fp_flag = False
    line_count = 0
    so_data = {"answers": [], "questions": []}
    invalid = False
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
                    return 1
                if not fp_flag:
                    return 1
            if dl_flag:
                if row[dl_key] != "TRUE":
                    line_count = line_count + 1
                    continue
            if len(row[so_key]) == 0:
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
                so_item["dest"] = os.path.join(output_folder, row[fp_key].split('.')[0], "sc_file.java")
            except ValueError:
                if not invalid:
                    invalid = True
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
    if invalid:
        return 2
    print("Processed {0} line(s).".format(line_count))
    print("Got {0} ids comprised of {1} answer-ids and {2} question-ids.\n"
          .format((len(so_data["answers"]) + len(so_data["questions"])),
                  len(so_data["answers"]), len(so_data["questions"])))
    return so_data


def save_as_snippets(snippets, so_items, nid, direct_link=True, aid=-1, verbose=False, copy=True):
    """
    Saves the snippets gotten from answers.

    :param snippets: a list of code snippets
    :param so_items: a list of stackoverflow entities
    :param nid: the id of the original entity. Either a question(this downloads snippets from its answers) or an answer
    :param direct_link: whether the snippets are from the original entity(True) or its answers(False)
    :param aid: the id of the answer. If it wasn't a direct link
    :param verbose: print more data
    :param copy: wheter the original java file should copied as well
    :return: a dict containg the statistics of the saving process. keys=["downloaded", "saved", "no_snippets"]
    """
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
    """
    Saves the snippets gotten from questions.

    :param snippets: a list of code snippets
    :param so_items: a list of stackoverflow entities
    :param nid: the id of the question entity
    :param verbose: print more data
    :param copy: whether the original java file should copied as well
    :return: a dict containing the statistics of the saving process. keys=["downloaded", "saved", "no_snippets"]
    """

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
    """
    Get the code snippets from stackoverflow answer entities

    :param so: the connection to the stackoverlflow api
    :param so_data: a dict containing the answer ids
    :param verbose: print more data
    :return: a dict containing the statistics of the saving process. keys=["downloaded", "saved", "no_snippets"]
    """
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
    """
    Get the code snippets from stackoverflow question entities and its answers

    :param so: the connection to the stackoverlflow api
    :param so_data: a dict containing the question ids
    :param accepted: whether only the accepted answer or the best voted one should be saved
    :param best: whether only the best voted answer should be saved
    :param verbose: print more data
    :return: a dict containing the statistics of the saving process. keys=["downloaded", "saved", "no_snippets"]
    """
    downloaded = 0
    saved = 0
    no_snippets = 0
    for count, chunk in enumerate(list(chunks(so_data["questions"], 100))):
        q_ids = []
        for so_item in chunk:
            q_ids.append(so_item.so_id)
        questions = so.questions(q_ids, pagesize=100)
        # wait for questions to load
        time.sleep(1)
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
    """
    get code snippets from only one stackoverflow answer

    :param so: connection to the stackoverlow api
    :param e_id: id of the stackoverflow entity
    :param question: whether the snippets of a question should be downloaded
    :param best: instead of the question get snippets from the best voted answer
    :param accepted: instead of the question get the snippets from the accepted answer
    :param output_file: the name of the file the snippet(s) should be saved to
    :param verbose: print more data
    :return: if the saving was a success returns 0. if not this function returns -1.
    """
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
