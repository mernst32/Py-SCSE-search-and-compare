class StackOverflowItem:
    """
    Object representing a Stackoverlow entity
    """
    def __init__(self, so_id, i_type, src, dest):
        """

        :param so_id: id of the SO entity
        :param i_type: the type of the SO entity: answer, question
        :param src: from where the link for this entity comes from
        :param dest: where the code snippet gotten from this entity should be saved
        """
        self.so_id = so_id
        self.i_type = i_type
        self.src = src
        self.dest = dest

    def print_obj(self):
        """
        Prints a representation of the entity
        """
        print("Obj@StackOverflowItem: [so_id={0}, i_type={1}, src={2}, dest={3}]"
              .format(self.so_id, self.i_type, self.src, self.dest))


def get_accepted_answer(question):
    """
    Returns the accepted answer from a question object
    :param question: a question object
    :return: the accepted answer object or none if there weren't any
    """
    answers = question.answers
    for a in answers:
        if a.accepted:
            return a
    return None


def get_best_answer(question):
    """
    Returns the highest voted answer from a question object
    :param question: a question object
    :return: the highest voted answer or none if there weren't any
    """
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
    """
    Returns all answers from a question object
    :param question: a question object
    :return: a list of all the answers or None if there are no answers
    """
    answers = question.answers
    if len(answers) > 0:
        return answers
    else:
        return None


def remove_dupl(a_list):
    """
    Remove duplicates from a list and returns the list
    :return: the list with only unique elements
    """
    return list(dict.fromkeys(a_list))


def chunks(a_list, n):
    """
    Breaks a list into n size chunks
    :param a_list: the list to be broken up
    :param n: the size of chunks
    :return: yields the chunks one after the other
    """
    for i in range(0, len(a_list), n):
        yield a_list[i:i + n]
