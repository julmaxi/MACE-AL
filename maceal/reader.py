from collections import namedtuple

Token = namedtuple("Token", "form sentence global_index")


class Token:
    def __init__(self, form, sentence, global_index, pos=None):
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


def read_sentence_file(fname, format="line"):
    if format == "line":
        return read_line_sentence_file(fname)
    elif format == "pipe":
        return read_pipe_sentence_file(fname)


def read_pipe_sentence_file(fname):
    sents = []
    curr_tok_idx = 0

    with open(fname) as f:
        for line_idx, line in enumerate(f):
            line = line.strip()
            if len(line) == 0:
                continue

            sent = Sentence()
            for raw_token in line.split():
                parts = raw_token.split("|")
                if len(parts) != 2:
                    raise RuntimeError(
                        "Token '{}'' in line {} is malformed (File: {})"
                        .format(raw_token, line_idx, fname))
                form, pos = parts

                sent.append_token(Token(form, sent, curr_tok_idx, pos=pos))
                curr_tok_idx += 1

            sents.append(sent)

    return sents


def read_line_sentence_file(fname):
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

                curr_sent.append_token(
                    Token(form, curr_sent, curr_tok_idx, **additional_attribs))

                curr_tok_idx += 1

        if len(curr_sent) > 0:
            sents.append(curr_sent)

    return sents


def repartition_sentences(gold_partition_sents, system_sents):
    flat_sys_tok_list = (tok for sent in system_sents for tok in sent)
    new_sentences = []
    for gold_sent in gold_partition_sents:
        new_sent = Sentence()
        for gold_tok in gold_sent:
            new_sent.append_token(next(flat_sys_tok_list))
        new_sentences.append(new_sent)

    return new_sentences


def read_annotation_files(files, annotation_file_format="line", check_integrity=True, plaintext_filename=None):
    prediction_tables = []
    sentences = None
    ref_filename = None

    if plaintext_filename is not None:
        sentences = read_sentence_file(plaintext_filename)
        ref_filename = plaintext_filename

    for filename in files:
        sents = read_sentence_file(filename, format=annotation_file_format)
        if sentences is None:
            sentences = sents
            ref_filename = filename
        else:
            repartition_sentences(sentences, sents)
        if check_integrity:
            for sent_idx, (new_sent, ref_sent) in enumerate(zip(sents, sentences)):
                for tok_idx, (new_tok, ref_tok) in enumerate(zip(new_sent, ref_sent)):
                    if new_tok.form != ref_tok.form:
                        raise RuntimeError("Sentences do not match in files {} and {} at sentence {} token {} ({} != {})".format(
                            ref_filename,
                            filename,
                            sent_idx,
                            tok_idx,
                            ref_tok.form,
                            new_tok.form
                        ))

        prediction_tables.append([tok.pos for sent in sents for tok in sent])

    return prediction_tables, sentences


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
