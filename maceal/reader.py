from collections import namedtuple

Token = namedtuple("Token", "form sentence global_index")

class Token:
    def __init__(self, form, sentence, global_index, pos = None):
        self.form = form
        self.sentence = sentence
        self.global_index = global_index
        self.pos = pos

class Sentence:
    def __init__(self):
        self.tokens = []

    def __iter__(self):
        return iter(self.tokens)

    def __len__(self):
        return len(self.tokens)

    def append_token(self, tok):
        self.tokens.append(tok)

    @property
    def raw_text(self):
        return " ".join(map(lambda x: x.form, self.tokens))

def read_sentence_file(fname):
    sents = []
    curr_sent = None
    curr_tok_idx = 0

    with open(fname) as f:
        for line in f:
            line = line.strip()

            if curr_sent is None:
                curr_sent = Sentence()

            if len(line) == 0:
                sents.append(curr_sent)
                curr_sent = None
            else:
                components = line.split()
                additional_attribs = {}
                if len(components) == 2:
                    form = components[0]
                    additional_attribs["pos"] = components[1]
                else:
                    form = line

                curr_sent.append_token(Token(form, curr_sent, curr_tok_idx, **additional_attribs))

                curr_tok_idx += 1

        if len(curr_sent) > 0:
            sents.append(curr_sent)

    return sents
                

def read_tab_file(filename):
    result = []
    with open(filename) as f:
        for line in f:
            result.append(line.strip().split())

    return result

def read_line_file(filename):
    result = []
    with open(filename) as f:
        for line in f:
            result.append(line.strip())

    return result