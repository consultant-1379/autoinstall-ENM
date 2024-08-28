There are three scripts in this directory:
(1) process_enminst.py
This is used to process an enminst log file and extract the plan.
(2) process_litpshow.py
This is used to process the output of litp show_plan command.
In this case it's expected that the user has issued the command and
placed the output into a file for processing.
(3) process_metrics.py
This is used to process the metrics log file.

(1) process_enminst.py example usage
$ python process_enminst.py -h
usage: process_enminst.py [-h] [-f FILE_NAME] [-force]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE_NAME, --file FILE_NAME
                        ENM Logfile to process
  -force, --force_one_line
                        Print details on one line. Truncates Info.

Examples:
python process_enminst.py -f enminst.log
python process_enminst.py -f enminst.log --force_one_line
python process_enminst.py -f ~/Downloads/enminst_4_clusters.log --force_one_line

(2) process_litpshow.py example usage
$ python process_litpshow.py -h
usage: process_litpshow.py [-h] [-f FILE_NAME] [-force]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE_NAME, --file FILE_NAME
                        litp show_plan Logfile to process
  -force, --force_one_line
                        Print details on one line. Truncates Info.

Examples:
python process_litpshow.py -f show_plan.log
python process_litpshow.py -f show_plan.log --force_one_line
python process_litpshow.py -f ~/Downloads/show_plan.log --force_one_line

(3) process_metrics.py example usage
$ python process_metrics.py -h
usage: process_metrics.py [-h] [-f FILE]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  litp metrics log to process

Examples:
python process_metrics.py -f metrics.log
python process_metrics.py -f ~/Downloads/metrics.log

