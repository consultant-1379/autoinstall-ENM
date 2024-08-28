'''
Module to analyze the metrics and the messages log, and analyse the
task length and phase lengths.
'''
import re
import sys
import os
from datetime import datetime

# pylint: disable=too-many-arguments
# pylint: disable=C0103
def log(text):
    '''
    Output log data to stdout
    '''
    sys.stdout.write(text + "\n")

if sys.argv[1] == '-h':
    print("\n\nUse this script as follows:\n\n" +
          "Call this script as follows\n\n" +
          "\"python analyze_plan_logs.py metrics.log messages " +
          "2>/tmp/table.html  1> /tmp/analyze_plan_logs.log\"\n\n" +
          "Then using a web browser open the file /tmp/table.html \n\n\n")
    sys.exit()
else:
    if 'metrics.log' not in sys.argv[1].split('/')[-1]:
        sys.stdout.write('Argument passed for metrics file locatiton \'{0}\' ' \
            'does not contain the partial string \'metrics.log\' as expected,' \
            ' will exit program.').format(sys.argv[1].split('/')[-1])
        sys.exit()


    if 'messages' not in sys.argv[2].split('/')[-1]:
        sys.stdout.write('Argument passed for messages file locatiton \'{0}\' ' \
            'does not contain the partial string \'messages\' as expected,' \
            ' will exit program.').format(sys.argv[1].split('/')[-1])
        sys.exit()

METRICSFILE = sys.argv[1]
MESSAGESFILE = sys.argv[2]

PHASE_TOKEN = 'phase'

for fp in (METRICSFILE, MESSAGESFILE):
    if not os.path.exists(fp):
        log("File missing: %s" % fp)
        sys.exit(1)

class Plan(object):
    '''
    This object is a particular plan found in the messages
    logs.

    Args:
        StartOfPlanDate (str): The date of the beginning of the plan run.
        StartOfPlanTime (str): The time of the beginning of the plan run.
        StartOfPlanLineNumber (int): The line number where the plan run begins.
        PlanNumber (int): If multiple plans are found in  the messages log,
                          this refers to it's number.
        EndPlanDate (str): The date of the end of the plan run.
        EndOfPlanTime (str): The time of the end of the plan run.
        EndOfPlanLineNumber (int): The line number where the plan run ends.
        PlanType (str): Info about the  outcome of the plan.
    '''
    def __init__(self, StartOfPlanDate, StartOfPlanTime,
                 StartOfPlanLineNumber, PlanNumber, EndPlanDate,
                 EndOfPlanTime, EndOfPlanLineNumber, PlanType):
        self.StartOfPlanDate = StartOfPlanDate
        self.StartOfPlanTime = StartOfPlanTime
        self.StartOfPlanLineNumber = StartOfPlanLineNumber
        self.PlanNumber = PlanNumber
        self.EndPlanDate = EndPlanDate
        self.EndOfPlanTime = EndOfPlanTime
        self.EndOfPlanLineNumber = EndOfPlanLineNumber
        self.PlanType = PlanType
        self.StartOfPlanDateMetricsFormat = None
        self.EndPlanDateMetricsFormat = None
        self.PhaseCount = None

    def getDateMetricsFormat(self, date_val):
        """
        Turns date from metrics format ie Jul 3 to metrics format
            2019-07-03
        Args:
            date_val (str): A string that represents a date value
                            retrieved from messages file.
        Returns:
            The date represented in the argument after it has been turned
                into the yyyy-mm-dd format.
        """
        def month__3L_abbrev_Num(string_mon):
            """
            Takes a 3 letter string argument for month, and
                returns a the months integer value.
            Args:
                string_mon (str): A 3 letter string argument for month

            Returns:
                mon_num (str): Months integer value as a string.
            """
            mont_dict = {
                'jan': '01',
                'feb': '02',
                'mar': '03',
                'apr': '04',
                'may': '05',
                'jun': '06',
                'jul': '07',
                'aug': '08',
                'sep': '09',
                'oct': '10',
                'nov': '11',
                'dec': '12'
            }
            monthstr = string_mon[:3].lower()
            mon_num = mont_dict[monthstr]
            return mon_num

        def ret_plan_day_of_month(date):
            """
            Returns the day portion of the date for the date supplied. Using
                two digits.

            Args:
                date (str): A string for the date in the messages file format.

            Returns: The day of month for the date, using two digits. ie. '07'
            """
            day = str(date.split()[1])
            if len(day) == 1:
                day = '0' + day
            return day

        year = datetime.now().year
        mon = month__3L_abbrev_Num(date_val)
        day_of_mon = ret_plan_day_of_month(date_val)
        date_metrics_format = str(year) + '-' + mon + '-' + day_of_mon
        return date_metrics_format


class Task(object):
    '''
    This object is a task object.

    Parameters:
        phase (int): The phase number.
        item (str): The item in the LITP model being acted upon by the task.
        info (str): Info about the task's behaviour
    '''
    def __init__(self, phase):
        self.phase = phase
        self.item = ''
        self.info = ''

    def __repr__(self):
        return "T: %s, %s" % (self.item, self.info)

    def to_html(self, idx):
        '''
        Description:
            Turn a task into a partial html table element containing data
                about a task object.

        Args:
            idx (int): An integer representing the index of a particular task in
                       an object.
        Returns:
            A partial html table element containing data about a task object
        '''
        return "<td>%d</td><td>%s</td><td>%s</td>" % (
            idx, self.item, self.info)


class Phase(object):
    '''
    An object that represents a phase in aplan.

    Args:
        date (str): The date of the end of the phase.
        time (str): The time at the end of the phase.
        phase (str): The number of the phase

    '''
    def __init__(self, date, time, phase):
        self.phase = phase
        self.date = date
        self.time = time
        self.tasks = []

    def to_html(self):
        html = '<td>%s</td><td>%s</td><td>%s</td>' % (
            self.date, self.time, self.phase)
        other_attrs = sorted([attr for attr in self.__dict__.keys()
                              if attr not in ('phase',
                                              'date',
                                              'time',
                                              'tasks')])
        if other_attrs:
            html += "<td><table border=solid><tr><th>Attribute"\
                        "</th><th>Value</th></tr>"
            for attr in other_attrs:
                html += "<tr><td>%s</td><td>%s</td></tr>" % (attr,
                                                             getattr(self,
                                                                     attr, ''))
            html += "</table></td>"
        if self.tasks:
            html += "<td><table border=solid><tr><th>Task</th>\
                     <th>Item</th><th>Info</th></tr>"
            for idx, task in enumerate(self.tasks, start=1):
                html += '<tr>%s</tr>' % task.to_html(idx)
            html += "</table></td>"
        return html

    def __repr__(self):
        return 'P: ' + ', '.join("%s=%s" % (attr, getattr(self, attr, ''))
                                 for attr in sorted(self.__dict__.keys()))

    @staticmethod
    def gen_html(phases):
        '''
        A static method to generate html code for the body of the web page.
            This contains data on the phases and tasks.

        Args:
            phases (dict): A dictionary containing phase objects.

        returns: html code for the body of the web page.
            This contains data on the phases and tasks.
        '''
        html = '<table border=solid>' +\
               '<tr><th>Date</th><th>Time</th><th>Phase</th><th>' \
                    'Extras</th><th>Tasks</th></tr>'
        for idx, phase in sorted(phases.items(),
                                 key=lambda item:
                                 int(item[0])):
            html += '<tr>%s</tr>' % phase.to_html()
        html += '</table>'
        return html


def manage_phase(phases, the_phase, parts):
    '''
    Returns a phase object.

    Args:
        phases (dict): A dictionary containing phase objects.
        the_phase (int): The individual phase number for object to be managed.
        parts (list): A list of elements that can be used to define a phase.
 
    Returns: A phase object
    '''
    if the_phase:
        phases[the_phase.phase] = the_phase

    if parts:
        return Phase(parts[f1_metrics_tokens[0]],
                     parts[f1_metrics_tokens[1]],
                     parts[f1_metrics_tokens[2]])


def get_phase_by_id(phases, parts):
    '''
    Description:
        Get the phase object by the ID
    Args:
        phases (dict): A dictionary containing phase objects.
        parts (list): A list of elements of a phase.
    '''
    try:
        return phases[parts[PHASE_TOKEN]]
    except KeyError as e:
        print e.message, e.args
        return None

the_phase = None
phases = {}


f2_A_NONE = 'NONE'
f2_A_BEGUN = 'BEGUN'
f2_A_IN_PHASE = 'IN_PHASE'
f2_A_IN_TASK = 'IN_TASK'
f2_A_IN_ENDPLAN = 'IN_ENDPLAN'
f2_A_ENDED = 'ENDED'

f2_A_show_tokens = [PHASE_TOKEN, 'item', 'info', 'extra']
f2_A_preamble = r'^(?P<date>[a-zA-Z]{3} +\d{1,2})' +\
                     ' +(?P<time>\\d{2}:\\d{2}:\\d{2}) +(?P<host>[^ ]+)' +\
                     ' enminst +INFO +monitorinfo +: +'
f2_A_phase_count_pattern = r'Total Phases: 61 *$'
f2_A_patterns = {'PlanBegin': r'SHOW_PLAN BEGIN *$',
                 'PlanEnd': r'SHOW_PLAN END *$',
                 'BeginningShowEndPlan': r'RUN_PLAN END *$',
                 'PlanType': r'(Plan completed successfully.' +\
                     '|RUN_PLAN BEGIN) *$',
                 'PlanTasksCompleted': r'Initial: 0 | Running: 0 *$',
                 'PlanComplete': r'Plan completed successfully. *$',
                 'PlanBegun': r'RUN_PLAN BEGIN *$',
                 'PhaseCount': r'Total\sPhases:\s+\d{1,4}\s+\|\sActive\s' +\
                     '+Phase\\(s\\):\\s+-\\s+\\|\\s+PlanState:' +\
                     '\\s+successful +'}

plan_start_time = []
plan_start_date = []
plan_start_line_num = []
plan_end_time = []
plan_end_date = []
plan_end_line_num = []
plan_type_list = []
phasecount_list = []

list_plan_objs = []


with open(MESSAGESFILE) as file_handle2A:
    file2A_data = file_handle2A.read()

    regexps = {k: re.compile(f2_A_preamble + pattern) for (k, pattern) in
               f2_A_patterns.items()}

    f2_A_state = f2_A_NONE
    the_phase = None
    the_task = None

    list_plan_objs = []

    for lineno, line in enumerate(file2A_data.splitlines(), start=1):
        line = line.strip()
        matches = {k: regexp.match(line) for (k, regexp) in regexps.items()}
        if matches['PlanBegin'] and f2_A_state not in f2_A_IN_ENDPLAN:
            if f2_A_state not in (f2_A_NONE, f2_A_ENDED):
                log("%d: ERROR: Begun Plan show while already " +\
                        "processing a Show" % lineno)
                sys.exit(1)
            f2_A_state = f2_A_BEGUN
            the_phase = None
            log("%d: BEGIN Plan Show" % lineno)
            plan_start_line_num.append(lineno)
            parts = matches['PlanBegin'].groupdict()
            time = parts['time']
            plan_start_time.append(time)
            date = parts['date']
            plan_start_date.append(date)
            plan_type_list.append(' ')
        elif matches['BeginningShowEndPlan']:
            f2_A_state = f2_A_IN_ENDPLAN
        elif matches['PlanEnd'] and f2_A_state in f2_A_IN_ENDPLAN:
            plan_end_line_num.append(lineno)
            log("%d: END Plan Show" % lineno)
            parts = matches['PlanEnd'].groupdict()
            time = parts['time']
            plan_end_time.append(time)
            date = parts['date']
            plan_end_date.append(date)
            f2_A_state = f2_A_ENDED

        elif f2_A_state == f2_A_ENDED:
            if  matches['PlanComplete']:
                plan_type_list = plan_type_list[:-1]
                plan_type_list.append('End_of_Plan')
            elif matches['PlanBegun']:
                plan_type_list = plan_type_list[:-1]
                plan_type_list.append('Plan_Begun')
            f2_A_state = f2_A_NONE


table_data = [['Start of \nplan Date',
               'Start of plan \nDate metrics \nformat',
               'Start of \nplan Time',
               'Start of plan \nLine Number',
               'Plan number',
               'End of \nplan Date',
               'End of \nplan Date \nin metrics format',
               'End of \nplan Time',
               'End of plan \nLine Number',
               'Plan Type',
               'PhaseCount']]

for i in xrange(len(plan_end_line_num)):
    Plan_obj = Plan(plan_start_date[i],
                    plan_start_time[i],
                    plan_start_line_num[i],
                    i,
                    plan_end_date[i],
                    plan_end_time[i],
                    plan_end_line_num[i],
                    plan_type_list[i])
    list_plan_objs.append(Plan_obj)

    setattr(list_plan_objs[i],
            'StartOfPlanDateMetricsFormat',
            list_plan_objs[i].getDateMetricsFormat(
                list_plan_objs[i].StartOfPlanDate))
    setattr(list_plan_objs[i],
            'EndPlanDateMetricsFormat',
            list_plan_objs[i].getDateMetricsFormat(
                list_plan_objs[i].EndPlanDate))

### Assume last plan in messages log is the  plan of interest.
planObject = list_plan_objs[len(list_plan_objs) - 1]

f1_metrics_tokens = ['date', 'time', PHASE_TOKEN, 'attrname', 'attrval']

f1_preamble_pattern = (r'^(?P<%s>\d{4}-\d{2}-\d{2}) +' + \
                       r'(?P<%s>\d{2}:\d{2}:\d{2}\.\d{3})') % \
                       (f1_metrics_tokens[0], f1_metrics_tokens[1])

f1_phase_pattern = f1_preamble_pattern + \
                   (r',\[LITP\]\[PLAN\]\[Run\]' + \
                    r'\[Phase(?P<%s>\d+)\]\.' + \
                    r'(?P<%s>[^=]+)=(?P<%s>[0-9.]+) *$') % \
                    (f1_metrics_tokens[2],
                     f1_metrics_tokens[3],
                     f1_metrics_tokens[4])

phase_time_list = []
with open(METRICSFILE) as file_handle1:
    file1_data = file_handle1.read()
    regexp = re.compile(f1_phase_pattern)

    for line in file1_data.splitlines():
        line = line.strip()
        match = regexp.search(line)
        if match:
            parts = match.groupdict()
            plan_start_datetime = datetime.strptime(
                planObject.StartOfPlanDateMetricsFormat + ' ' +
                planObject.StartOfPlanTime, "%Y-%m-%d %H:%M:%S")
            plan_end_datetime = datetime.strptime(
                planObject.EndPlanDateMetricsFormat + ' ' +
                planObject.EndOfPlanTime, "%Y-%m-%d  %H:%M:%S")
            if ((datetime.strptime(parts['date'] + ' ' + parts['time'][0:8],
                                   "%Y-%m-%d %H:%M:%S") >= plan_start_datetime)
                    and (datetime.strptime(parts['date'],
                                           "%Y-%m-%d") <= plan_end_datetime)):
                if parts:
                    if all(token in parts.keys() for token in
                           f1_metrics_tokens):
                        if not the_phase \
                            or getattr(the_phase,
                                       PHASE_TOKEN, '') != parts[PHASE_TOKEN]:
                            the_phase = manage_phase(phases,
                                                     the_phase,
                                                     parts)
                        setattr(the_phase,
                                parts[f1_metrics_tokens[3]],
                                parts[f1_metrics_tokens[4]])
    manage_phase(phases, the_phase, [])

f2_NONE = 'NONE'
f2_BEGUN = 'BEGUN'
f2_IN_PHASE = 'IN_PHASE'
f2_IN_TASK = 'IN_TASK'
f2_ENDED = 'ENDED'

f2_show_tokens = [PHASE_TOKEN, 'item', 'info', 'extra']
f2_preamble = r'^(?P<date>[a-zA-Z]{3} +\d{1,2}) ' +\
               '+(?P<time>\\d{2}:\\d{2}:\\d{2}) ' +\
               '+(?P<host>[^ ]+) enminst +INFO +monitorinfo +: +'
f2_patterns = {'PlanBegin': r'SHOW_PLAN BEGIN *$',
               'PlanEnd': r'SHOW_PLAN END *$',
               'PlanTotals': r'Total Phases: +\d+ +',
               'PhaseStart': (r'Phase +(?P<%s>\d+) +tasks: *$'
                              % f2_show_tokens[0]),
               'TaskStart': r'Task: +(Initial|Success) *$',
               'TaskItem': (r'Item: +(?P<%s>.+) *$' % f2_show_tokens[1]),
               'TaskInfo': (r'Info: +(?P<%s>.+) *$' % f2_show_tokens[2]),
               'TaskInfoMore': (r'(?P<%s>.*)$' % f2_show_tokens[3])}

with open(MESSAGESFILE) as file_handle2:
    file2_data = file_handle2.read()

    regexps = {k: re.compile(f2_preamble + pattern)
               for (k, pattern) in f2_patterns.items()}

    f2_state = f2_NONE
    the_phase = None
    the_task = None

    for lineno, line in enumerate(file2_data.splitlines(), start=1):

        if lineno >= planObject.EndOfPlanLineNumber or \
                lineno <= planObject.StartOfPlanLineNumber:
            continue
        line = line.strip()
        matches = {k: regexp.match(line) for (k, regexp) in regexps.items()}
        if matches['PlanBegin']:
            if f2_state not in (f2_NONE, f2_ENDED):
                log("%d: ERROR: Begun Plan show while already " +\
                    "processing a Show" % lineno)
                sys.exit(1)
            f2_state = f2_BEGUN
            the_phase = None
            log("%d: BEGIN Plan Show" % lineno)
        elif matches['PlanEnd'] or matches['PlanTotals']:
            if f2_state in (f2_BEGUN, f2_IN_PHASE, f2_IN_TASK):
                f2_state = f2_ENDED
                if the_phase and the_task:
                    the_phase.tasks.append(the_task)
                the_phase = None
                the_task = None
                log("%d: END Plan Show" % lineno)
                break
        elif matches['PhaseStart']:
            parts = matches['PhaseStart'].groupdict()
            if parts and f2_show_tokens[0] in parts.keys():
                if f2_state == f2_BEGUN:
                    f2_state = f2_IN_PHASE
                    the_phase = get_phase_by_id(phases, parts)
                    log("%d: Started phase %s" % (lineno,
                                                  parts[f2_show_tokens[0]]))
                elif f2_state in (f2_IN_PHASE, f2_IN_TASK):
                    if the_phase:
                        log("%d: Finished with phase %s" % (lineno,
                            getattr(the_phase, f2_show_tokens[0], '')))
                        if f2_state == f2_IN_TASK and the_task:
                            the_phase.tasks.append(the_task)
                            the_task = None
                    the_phase = get_phase_by_id(phases, parts)
                    if the_phase:
                        log("%d: Transitioning to phase %s, %s" % \
                            (lineno, parts[f2_show_tokens[0]], the_phase))
                    else:
                        log("Failed to find phase %s" %
                            parts[f2_show_tokens[0]])
        elif matches['TaskStart']:
            if f2_state in (f2_IN_PHASE, f2_IN_TASK) and the_phase:
                parts = matches['TaskStart'].groupdict()
                if parts and all(key in parts.keys()
                                 for key in ('date', 'time')):
                    if not the_task:
                        log("%d: New task for phase %s" % \
                            (lineno, the_phase.phase))
                    else:
                        the_phase.tasks.append(the_task)
                        log("%d: Completed task %d for phase %s, %s" % \
                            (lineno,
                             len(the_phase.tasks),
                             the_phase.phase,
                             the_task))
                    the_task = Task(the_phase)
                    f2_state = f2_IN_TASK
        elif matches['TaskItem']:
            if f2_state == f2_IN_TASK and the_phase and the_task:
                parts = matches['TaskItem'].groupdict()
                if parts and f2_show_tokens[1] in parts.keys():
                    the_task.item = parts[f2_show_tokens[1]]
                    log("%d: Item %s found for task" % (lineno, the_task.item))
        elif matches['TaskInfo']:
            if f2_state == f2_IN_TASK and the_phase and the_task:
                parts = matches['TaskInfo'].groupdict()
                if parts and f2_show_tokens[2] in parts.keys():
                    the_task.info = parts[f2_show_tokens[2]]
        elif matches['TaskInfoMore']:
            if f2_state == f2_IN_TASK and the_phase and the_task:
                parts = matches['TaskInfoMore'].groupdict()
                if parts and f2_show_tokens[3] in parts.keys():
                    if the_task.info:
                        the_task.info += ' '
                    the_task.info += parts[f2_show_tokens[3]]

HTMLTITLE = 'Metrics and Messages parsing'
PLAN_DATA = '<td>The plan being analysed begins at <b>%s</b> on <b>%s</b>' % (Plan_obj.StartOfPlanTime, Plan_obj.StartOfPlanDate) + \
            ' and ends at <b>%s</b> on <b>%s<b>.</td>' % (Plan_obj.EndOfPlanTime, Plan_obj.EndPlanDate)

HTMLHDR = '<html>' + \
          ('<title>%s</title>' % HTMLTITLE) + \
          ('<header><center>%s</center></header><HR>' % HTMLTITLE) + \
          ('<header>Input files:<BR>%s<BR>%s<BR></header><HR>'
           % (METRICSFILE, MESSAGESFILE)) + \
          ('<header>%s</header>' % PLAN_DATA) +'<body>'

HTML_BODY = Phase.gen_html(phases)
HTML_FTR = '</body></html>'

sys.stderr.write(HTMLHDR + HTML_BODY + HTML_FTR)
