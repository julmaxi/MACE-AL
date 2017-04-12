*  starten des tools (mit active learning)
bash run_al.sh

*  run_al.sh calls startErrorCorrection.py:

python src/startErrorCorrection.py -p dir-with-annot-predictions -g [gold-file|False] -e [True|False] -r 1 -f feedback   

*  -p directory that contains the annotators' predictions
*  -g file with gold annotations (if exists)
*  -e print logfile with entropies for each iteration [True|False]
*  -r number of restarts with random initialisations (set to 1 because of time constraints during AL)
*  -f should the model consider the oracle's feedback? (yes, of course ;)


*  entfernen der temporären files und der Logdatei
bash clean.sh



*  input data for POS tagging
*  one file per annotator (suffix: .pred), format: word\tprediction
*  gold file for evaluation (if no gold annotations exist, we need a file with one word form per line,
*  and newlines that indicate sentence splits)

*  Example:
*  data/answers
*  annotator predictions:
	answers.bilstm.pred  
	answers.stan.pred  
	answers.tree.pred  
	answers.wapiti.pred
	answers.hun.pred   
	answers.svm.pred   
	answers.tweb.pred

*  gold file:
	answers.exp02.gold

*  file with word forms and sentence splits:
	answers.exp02.txt

**** 
*  src/util.py and src/sentences.py => read the input, extract sentences, get annotation from the oracle...
*  src/util.py 	   => 	def readPredictions( path ) 
*  src/sentences.py =>	def getAnnotation(...)
*  ...
