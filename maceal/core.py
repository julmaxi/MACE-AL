import os
import os.path as path
import tempfile
import shutil

import random

from collections import namedtuple

from itertools import izip

import reader

MaceResult = namedtuple("MaceResult", "predictions competences entropies")

def argmax(l, blacklist = []):
    assert len(l) > 0, "Can not compute maximum of empty list"
    max_idx = None
    max_val = None

    for idx, val in enumerate(l):
        if idx in blacklist:
            continue
        if max_idx is None:
            max_idx = idx
            max_val = val
        elif max_val < val:
            max_idx = idx
            max_val = val

    return max_idx


class MaceRunner:
    """
    Runs Mace Command
    """

    def __init__(self, jar_path = "MACE.jar", **kwargs):
        self.jar_path = jar_path
        self.preset_args = kwargs

    def run_mace(self, predictions_filename, **kwargs):
        """
        Runs a mace command and returns the results
        """
        args = dict(self.preset_args)

        for key, val in kwargs.items():
            args[key] = val

        outdir = tempfile.mkdtemp()
        #TODO: Cross plattform -> do not redirect to unix specific place
        os.system(self._construct_command(path.join(outdir, "out"), predictions_filename, **args) + " > /dev/null")

        entropies = None
        if args.get("entropies", False):
            entropies_file = path.join(outdir, "out.entropies")
            entropies = list(map(float, reader.read_line_file(entropies_file)))

        competences_file = path.join(outdir, "out.competence")
        competences = list(map(float, reader.read_tab_file(competences_file)[0]))

        predictions_file = path.join(outdir, "out.prediction")
        predictions = reader.read_line_file(predictions_file)

        shutil.rmtree(outdir)

        return MaceResult(predictions, competences, entropies)

    def _construct_command(self,
                           prefix,
                           predictions_filename,
                           entropies = False,
                           controls = None,
                           restarts = None,
                           vanilla = False):
        arg_strings = []
        arg_strings.append('--prefix "{}"'.format(prefix))

        if entropies:
            arg_strings.append('--entropies')

        if controls is not None:
            arg_strings.append('--controls "{}"'.format(controls))

        if restarts is not None:
            arg_strings.append('--restarts {}'.format(int(restarts)))

        if vanilla:
            arg_strings.append('--em')

        return 'java -jar "{jar}" {args} {f}'.format(jar = self.jar_path, args = " ".join(arg_strings), f = predictions_filename)

AnnotationRequest = namedtuple("AnnotationRequest", "original_annotations token")

class AnnotationState:
    def __init__(self, raw_parser_predictions, token_sequence, mace_runner, use_feedback = True):
        self.numerical_mapper = CategorialToNumericConverter()
        self.parser_predictions = ParserPredictionTable(raw_parser_predictions)
        self.current_iteration = 0
        self.use_feedback = use_feedback
        self.mace_runner = mace_runner
        self.token_sequence = token_sequence

        self.request_blacklist = set()

        self.user_feedback = [None for _ in xrange(self.parser_predictions.num_tokens)]

        f, feedback_filename = tempfile.mkstemp()
        os.close(f)
        #f.close()
        self.feedback_filename = feedback_filename
        #self.replace_lowest_competence_annotator = replace_lowest_competence_annotator
        self.current_numeric_predictions = []

    def get_next_annotation_request(self):
        args = {}
        if self.use_feedback and self.current_iteration > 0:
            with open(self.feedback_filename, "w") as f:
                for user_feedback in self.user_feedback:
                    if user_feedback is not None:
                        f.write("{}".format(self.numerical_mapper.map_value(user_feedback)))
                    f.write("\n")

            args["controls"] = self.feedback_filename

        predictions, competences, entropies = self.mace_runner.run_mace(self.parser_predictions.dumpf(mapper = self.numerical_mapper), **args)
        self.current_numeric_predictions = predictions

        requested_index = argmax(entropies, self.request_blacklist)

        return AnnotationRequest(
                self.parser_predictions.get_all_predictions_at_index(requested_index),
                self.token_sequence[requested_index])

    def get_current_predictions(self):
        preds = []
        curr_sent_preds = []
        curr_sent = None

        for tok, pred in izip(self.token_sequence, self.current_numeric_predictions):
            if curr_sent is None:
                curr_sent = tok.sentence
            elif curr_sent != tok.sentence:
                preds.append(curr_sent_preds)

                curr_sent_preds = []
                curr_sent = tok.sentence
            pred_text = self.numerical_mapper.reverse_map_value(int(pred))
            curr_sent_preds.append((tok.form, pred_text))

        preds.append(curr_sent_preds)
        return preds

    def blacklist_request(self, request):
        self.request_blacklist.add(request.token.global_index)

    def process_annotation(self, request, annotation):
        annotator_replacement_index = random.randint(0, self.parser_predictions.num_annotators - 1)
        
        self.parser_predictions.set_prediction(annotator_replacement_index, request.token.global_index, annotation)
        self.user_feedback[request.token.global_index] = annotation

        self.current_iteration += 1

    def cleanup(self):
        os.remove(self.feedback_filename)
        self.parser_predictions.cleanup()

class CategorialToNumericConverter:
    def __init__(self):
        self.counter = 0
        self.reverse_map = []
        self.forward_map = {}

    def map_value(self, val):
        num_value = self.forward_map.get(val)

        if num_value is None:
            num_value =  self.counter
            self.forward_map[val] = num_value
            self.reverse_map.append(val)

            self.counter += 1

        return num_value

    def reverse_map_value(self, val):
        return self.reverse_map[val]

class ParserPredictionTable:
    def __init__(self, table):
        #TODO: Probably better to copy
        self.table = table

        self.fname = None

    def dumpf(self, mapper):
        if self.fname is None:
            f, fname = tempfile.mkstemp()
            os.close(f)
            self.fname = fname
        f = open(self.fname, "w")

        for rows in zip(*self.table):
            f.write(",".join(map(lambda x: str(mapper.map_value(x)), rows)))
            #f.write(",".join(map(lambda x: x.replace(",", ";"), rows)))
            f.write("\n")

        f.close()

        return self.fname

    def set_prediction(self, annotator_idx, token_idx, prediction):
        self.table[annotator_idx][token_idx] = prediction

    @property
    def num_annotators(self):
        return len(self.table)

    @property
    def num_tokens(self):
        return len(self.table[0])

    @property
    def value_set(self):
        result = set()

        for annotator in self.table:
            for tok in annotator:
                result.add(tok)

        return result

    def get_all_predictions_at_index(self, token_idx):
        result = []
        for annotator_row in self.table:
            result.append(annotator_row[token_idx])
        return result

    def cleanup(self):
        os.remove(self.fname)
