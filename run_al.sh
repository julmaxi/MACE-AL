#! /bin/bash

var=answers

python src/startErrorCorrection.py -p data/$var -g data/$var/$var.exp02.gold -e True -r 1 -f feedback 

#`bash ./clean.sh`

