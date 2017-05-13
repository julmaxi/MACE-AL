#from Tkinter import *
#from Tkinter import ttk
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

        if os.path.isdir(args.annotation_dir):
            preds = readPredictions(args.annotation_dir)
            sentences = reader.read_sentence_file(glob.glob(args.annotation_dir + "/*.txt")[0])
            flat_tok_list = [tok for sent in sentences for tok in sent]
            self.annotation_state = core.AnnotationState(preds, flat_tok_list, core.MaceRunner(entropies = True, restarts = args.mace_restarts))
        else:
            with open(args.annotation_dir, "rb") as f:
                self.annotation_state = cPickle.load(f)

        self.root = Tk()
        self.root.title("Mace AL")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        mainframe = ttk.Frame(self.root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky= N + W + E + S)
        mainframe.columnconfigure(1, weight=1)
        mainframe.rowconfigure(1, weight=1)

        self.user_tag_value = StringVar()
        self.prediction_string_value = StringVar()

        self.text_box = Text(mainframe, height = 2, font = ('TkDefaultText', 16), padx = 5, pady = 5)
        self.text_box.tag_configure('color', foreground='#FFFFFF', background="red", font=('TkDefaultText', 16, 'bold'))
        self.text_box.grid(column=1, row=1, columnspan = 3, sticky=(W, E))

        ttk.Label(mainframe, textvariable = self.prediction_string_value).grid(column=1, row=2, columnspan = 2, sticky=(W, E))

        self.combobox = ttk.Combobox(mainframe, textvariable = self.user_tag_value, values = sorted(self.annotation_state.parser_predictions.value_set))
        self.combobox.grid(column=1, row=3, sticky=W)
        ttk.Button(mainframe, text="Skip", command=self.skip_annotation).grid(column=2, row=3, sticky=E)
        ttk.Button(mainframe, text="Next", command=self.request_next_annotation).grid(column=3, row=3, sticky=E)

        self.comment_box = Text(mainframe, height = 2, font = ('TkDefaultText', 16), padx = 5, pady = 5)
        self.comment_box.grid(column=1, row=4, columnspan = 3, sticky=(W, E))

        #ttk.Label(mainframe, text="feet").grid(column=3, row=1, sticky=W)
        #ttk.Label(mainframe, text="is equivalent to").grid(column=1, row=2, sticky=E)
        #ttk.Label(mainframe, text="meters").grid(column=3, row=2, sticky=W)

        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        self.combobox.focus()
        self.root.bind('<Return>', self.request_next_annotation)
        

        menubar = Menu(self.root)
        self.root['menu'] = menubar
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(menu=file_menu, label='File')

        file_menu.add_command(label="Save", command=self.save_state)
        file_menu.add_command(label="Save Predictions", command=self.save_predictions)


    def run(self):
        self.get_next_request()
        self.root.mainloop()

    def skip_annotation(self):
        self.annotation_state.blacklist_request(self.current_request)

        comment_value = self.comment_box.get("1.0",END).strip()
        self.write_comment(self.current_request.token, comment_value)
        if self.autosave:
            self.save_state()

        self.get_next_request()

    def get_next_request(self):
        self.current_request = self.annotation_state.get_next_annotation_request()

        predicted_counts = Counter(self.current_request.original_annotations)
        prediction_strings = []
        for item, count in sorted(predicted_counts.items(), key = lambda e: (e[1], e[0])):
            prediction_strings.append("{} ({})".format(item, count))
        self.prediction_string_value.set("Predicted: " + ", ".join(prediction_strings))
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
            res = tkMessageBox.askokcancel("New Tag", "You are about to introduce the new tag '{}'. Proceed?".format(value))
            if res == False:
                return
            else:
                self.combobox.configure(values = sorted(list(self.annotation_state.parser_predictions.value_set) + [value]))

        self.annotation_state.process_annotation(self.current_request, value)

        comment_value = self.comment_box.get("1.0",END).strip()
        if len(comment_value) > 0:
            self.write_comment(self.current_request.token, comment_value, value)
            self.comment_box.delete("1.0", END)

        if self.autosave:
            self.save_state()

        self.get_next_request()

    def write_comment(self, token, comment, annotation = None):
            with open(self.comments_filename, "a") as f:
                if annotation is None:
                    annotation_text = "skipped"
                else:
                    annotation_text = annotation
                f.write('{}\t{}\t{}\t"{}"'.format(token.global_index, token.form, annotation_text, comment))
                f.write("\n")
    
    def save_state(self):
        with open(self.save_filename, "wb") as f:
            cPickle.dump(self.annotation_state, f)

    def save_predictions(self):
        f = tkFileDialog.asksaveasfile(mode='w')
        for sent_preds in self.annotation_state.get_current_predictions():
            f.write("\n".join(map(lambda t: "\t".join(t), sent_preds)))
            f.write("\n\n")        
        f.close()

def parse_args():
    parser = ArgumentParser()

    parser.add_argument("annotation_dir")
    parser.add_argument("--mace-restarts", type = int, default = 1)
    parser.add_argument("--comments-filename", default = "comments.txt")
    parser.add_argument("--save-filename", default = "maceal-state.pkl")
    parser.add_argument("--autosave", type = bool, default = True)

    return parser.parse_args()

if __name__ == "__main__":
    AnnotationGUI().run() 

