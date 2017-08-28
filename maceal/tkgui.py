import ttk
from Tkinter import *
import tkMessageBox
import tkFileDialog

from argparse import ArgumentParser
import glob

from collections import Counter

import os.path

import cPickle

import maceal.core as core
from util import readPredictions
import reader

user_tag = None
annotation_state = None
text_box = None


class AnnotationGUI:
    def __init__(self):
        args = parse_args()

        self.comments_filename = args.comments_filename
        self.save_filename = args.save_filename
        self.autosave = args.autosave

        mace_runner = core.MaceRunner(
                entropies=True,
                restarts=args.mace_restarts,
                jar_path=args.mace_path)

        if not os.path.isfile(args.save_filename):
            state = self._read_annotation_state_from_args(args)
        else:
            while True:
                print("Found a previous annotation file at {}".format(args.save_filename))
                response = raw_input("(C)ontiune or (O)verwrite?")
                if response.lower() == "c":
                    with open(args.save_filename, "rb") as f:
                        state = cPickle.load(f)
                    break
                elif response.lower() == "o":
                    state = self._read_annotation_state_from_args(args)
                    break
#                self.annotation_state = cPickle.load(f)

        self.annotation_state = core.AnnotationManager(
            state=state,
            mace_runner=mace_runner
        )

        self.root = Tk()
        self.root.title("Mace AL")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        mainframe = ttk.Frame(self.root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=N + W + E + S)
        mainframe.columnconfigure(1, weight=1)
        mainframe.rowconfigure(1, weight=1)

        self.user_tag_value = StringVar()
        self.prediction_string_value = StringVar()

        self.text_box = Text(mainframe, height=2, font=(
            'TkDefaultText', 16), padx=5, pady=5)
        self.text_box.tag_configure(
            'color',
            foreground='#FFFFFF',
            background="red",
            font=('TkDefaultText', 16, 'bold'))
        self.text_box.grid(column=1, row=1, columnspan=3, sticky=(W, E, N, S))
        self.text_box.bind("<Key>", lambda e: "break")

        ttk.Label(mainframe, textvariable=self.prediction_string_value).grid(
            column=1, row=2, columnspan=2, sticky=(W, E))

        self.combobox = ttk.Combobox(
            mainframe,
            textvariable=self.user_tag_value,
            values=sorted(self.annotation_state.parser_predictions.value_set))
        self.combobox.grid(column=1, row=3, sticky=W)
        ttk.Button(mainframe, text="Skip", command=self.skip_annotation).grid(
            column=2, row=3, sticky=E)
        ttk.Button(
            mainframe,
            text="Next",
            command=self.request_next_annotation).grid(
            column=3, row=3, sticky=E)

        comment_box_label = ttk.Label(mainframe, text="Comment")
        comment_box_label.grid(column=1, row=4, sticky=W)

        self.comment_box = Text(mainframe, height=2, font=(
            'TkDefaultText', 16), padx=5, pady=5)
        self.comment_box.grid(column=1, row=5, columnspan=3, sticky=(W, E))

        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        self.combobox.focus()
        self.root.bind('<Return>', self.request_next_annotation)

        menubar = Menu(self.root)
        self.root['menu'] = menubar
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(menu=file_menu, label='File')

        file_menu.add_command(label="Save", command=self.save_state)
        file_menu.add_command(label="Save Predictions",
                              command=self.save_predictions)

    def _read_annotation_state_from_args(self, args):
        if len(args.annotation_files) == 0:
            raise RuntimeError("No annotation files provided")

        preds, sentences = reader.read_annotation_files(
            args.annotation_files,
            annotation_file_format=args.annotation_file_format,
            plaintext_filename=args.plaintext_filename)
        flat_tok_list = [tok for sent in sentences for tok in sent]
        state = core.AnnotationState(preds, flat_tok_list)
        return state

    def run(self):
        self.get_next_request()
        self.root.mainloop()

    def on_close(self):
        self.root.destroy()
        self.annotation_state.cleanup()

    def skip_annotation(self):
        self.annotation_state.blacklist_request(self.current_request)

        comment_value = self.comment_box.get("1.0", END).strip()
        self.write_comment(self.current_request.token, comment_value)
        if self.autosave:
            self.save_state()

        self.get_next_request()

    def get_next_request(self):
        self.current_request = \
            self.annotation_state.get_next_annotation_request()
        if self.current_request is None:
            tkMessageBox.showinfo("End of Document", "The end of the document has been reached. No more annotations are possible.")
            return

        predicted_counts = Counter(self.current_request.original_annotations)
        prediction_strings = []
        for item, count in sorted(
                predicted_counts.items(),
                key=lambda e: (e[1], e[0])):
            prediction_strings.append("{} ({})".format(item, count))
        self.prediction_string_value.set(
            "Predicted: " + ", ".join(prediction_strings))
        self.present_token(self.current_request.token)

    def present_token(self, target_tok):
        self.text_box.delete("1.0", END)

        for tok in target_tok.sentence:
            if tok == target_tok:
                self.text_box.insert(END, tok.form, 'color')
            else:
                self.text_box.insert(END, tok.form)
            self.text_box.insert(END, " ")

    def request_next_annotation(self, *arg):
        value = self.user_tag_value.get()

        if value == "":
            self.root.bell()
            return

        if value not in self.annotation_state.parser_predictions.value_set:
            res = tkMessageBox.askokcancel(
                "New Tag",
                "You are about to introduce the new tag '{}'. Proceed?".format(value))
            if res is False:
                return
            else:
                self.combobox.configure(values=sorted(
                    list(self.annotation_state.parser_predictions.value_set) + [value]))

        self.annotation_state.process_annotation(self.current_request, value)

        comment_value = self.comment_box.get("1.0", END).strip()
        if len(comment_value) > 0:
            self.write_comment(self.current_request.token,
                               comment_value, value)
            self.comment_box.delete("1.0", END)

        if self.autosave:
            self.save_state()

        self.get_next_request()

    def write_comment(self, token, comment, annotation=None):
        with open(self.comments_filename, "a") as f:
            if annotation is None:
                annotation_text = "skipped"
            else:
                annotation_text = annotation
            f.write('{}\t{}\t{}\t"{}"'.format(token.global_index,
                                              token.form,
                                              annotation_text,
                                              comment))
            f.write("\n")

    def save_state(self):
        with open(self.save_filename, "wb") as f:
            cPickle.dump(self.annotation_state.state, f)

    def save_predictions(self):
        f = tkFileDialog.asksaveasfile(mode='w')
        for sent_preds in self.annotation_state.state.get_current_predictions():
            f.write("\n".join(map(lambda t: "\t".join(t), sent_preds)))
            f.write("\n\n")
        f.close()


def parse_args():
    parser = ArgumentParser(
        description="A small tool for Mace Active Learning Annotation")

    parser.add_argument(
        "annotation_files",
        nargs="*",
        help="Files containing system annotations")
    parser.add_argument(
        "--plaintext",
        default=None,
        dest="plaintext_filename",
        help="Tokenized plaintext containing sentence segmentation in a one-token-per-line format")
    parser.add_argument(
        "--format",
        type=str,
        default="line",
        choices=["pipe", "line"],
        dest="annotation_file_format",
        help="Format of the annotation files")

    parser.add_argument(
        "--mace-restarts",
        type=int, default=1,
        help="Number of restarts for mace")
    parser.add_argument(
        "--comments-filename",
        default="comments.txt", help="Target file for comments")
    parser.add_argument(
        "--save-filename",
        default="maceal-state.pkl",
        help="File to save annotations to. If the file at the specified path already exists, MaceAL will load the annotation state from this file.")
    parser.add_argument(
        "--autosave",
        default=True,
        action="store_true",
        help="Enable autosaving after each annotation (Default)")
    parser.add_argument(
        "--no-autosave",
        action="store_false",
        dest="autosave",
        help="Disable autosaving after each annotation")
    parser.add_argument(
        "--mace-path",
        default="MACE.jar",
        help="Path to the Mace jar file")

    args = parser.parse_args()

    return args


def main():
    AnnotationGUI().run()


if __name__ == "__main__":
    main()
