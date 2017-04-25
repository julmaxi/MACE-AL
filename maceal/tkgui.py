from tkinter import *
from tkinter import ttk

import maceal.core as core
from argparse import ArgumentParser
import glob

from util import readPredictions

user_tag = None
annotation_state = None
text_box = None


class AnnotationGUI:
    def __init__(self):
        args = parse_args()

        preds = readPredictions(args.annotation_dir)

        sentences = core.read_sentence_file(glob.glob(args.annotation_dir + "/*.txt")[0])
        flat_tok_list = [tok for sent in sentences for tok in sent]
        self.annotation_state = core.AnnotationState(preds, flat_tok_list, core.MaceRunner(entropies = True))


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

        self.text_box = Text(mainframe, height = 1)
        self.text_box.grid(column=1, row=1, columnspan = 2, sticky=(W, E))

        ttk.Label(mainframe, textvariable = self.prediction_string_value).grid(column=1, row=2, columnspan = 2, sticky=(W, E))

        ttk.Combobox(mainframe, textvariable = self.user_tag_value, values = list(self.annotation_state.parser_predictions.value_set)).grid(column=1, row=3, sticky=W)
        ttk.Button(mainframe, text="Next", command=self.request_next_annotation).grid(column=2, row=3, sticky=E)

        #ttk.Label(mainframe, text="feet").grid(column=3, row=1, sticky=W)
        #ttk.Label(mainframe, text="is equivalent to").grid(column=1, row=2, sticky=E)
        #ttk.Label(mainframe, text="meters").grid(column=3, row=2, sticky=W)

        for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

        self.text_box.focus()
        self.root.bind('<Return>', self.request_next_annotation)


    def run(self):
        self.get_next_request()
        self.root.mainloop()

    def get_next_request(self):
        self.current_request = self.annotation_state.get_next_annotation_request()

        self.prediction_string_value.set("Predicted: " + " ".join(self.current_request.original_annotations))
        self.present_token(self.current_request.token)

    def present_token(self, target_tok):
        self.text_box.delete("1.0", END)
        self.text_box.tag_configure('color', foreground='#FFFFFF', background="red", font=('Tempus Sans ITC', 12, 'bold'))

        for tok in target_tok.sentence:
            if tok == target_tok:
                self.text_box.insert(END, tok.form, 'color')
            else:
                self.text_box.insert(END, tok.form)
            self.text_box.insert(END, " ")
            
    def request_next_annotation(self, *arg):
        value = self.user_tag_value.get()

        self.annotation_state.process_annotation(self.current_request, value)
        self.get_next_request()
        

def parse_args():
    parser = ArgumentParser()

    parser.add_argument("annotation_dir")

    return parser.parse_args()

if __name__ == "__main__":
    AnnotationGUI().run() 

