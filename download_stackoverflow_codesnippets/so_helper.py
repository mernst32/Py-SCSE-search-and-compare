class StackOverflowItem:
    def __init__(self, so_id, i_type, src, dest):
        self.so_id = so_id
        self.i_type = i_type
        self.src = src
        self.dest = dest

    def print_obj(self):
        print("Obj@StackOverflowItem: [so_id={0}, i_type={1}, src={2}, dest={3}]"
              .format(self.so_id, self.i_type, self.src, self.dest))


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


def remove_dupl(a_list):
    return list(dict.fromkeys(a_list))


def chunks(a_list, n):
    for i in range(0, len(a_list), n):
        yield a_list[i:i + n]
