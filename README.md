# MACE-AL Annotation Tool

## Introduction

This is a small tool to conduct active learning experiments with mace.

## Usage
In order to use the tool you need to download the Mace jar file from [https://www.isi.edu/publications/licensed-sw/mace/] and place it in your working directory.

Run python setup.py install to install the tool in your local environment. This will also take care of all dependecies.
To run one of the examples type mace-al --format pipe examples/pipe/*.pred or mace-al --plaintext examples/line/plaintext.txt examples/line/*.pred

## Short Tutorial

You can use the drop-down textfield in the lower left corner to input the correct tag for the word highlighted above.
If you hit "Next" your choice will be recorded and MACE will be rerun to present the next edit.
You can also add a comment in the lower textfield which is recorded in the comments file (by default "comments.txt")
If yout hit "Skip", no annotation will be recorded and the instance will never be presented to you again. You can identify all skipped instances from the comments file.