# MACE-AL Annotation Tool

## Introduction

This is a small tool to conduct active learning experiments with mace.

## Usage
In order to use the tool you need to download the Mace jar file from [https://www.isi.edu/publications/licensed-sw/mace/] and place it in your working directory.

Run python setup.py install to install the tool in your local environment. This will also take care of all dependecies.
To run one of the examples type mace-al --format pipe examples/pipe/*.pred or mace-al --plaintext examples/line/plaintext.txt examples/line/*.pred
