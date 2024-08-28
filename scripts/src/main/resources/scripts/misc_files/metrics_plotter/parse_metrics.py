#!/usr/bin/env python

""" Script to process litp metrics log files and determine if there are any
    unexpected/unexplained delays between execution of phases.
    It outputs a Gnuplot configuration file 'plan_1_plot.cfg' which can be
    used to create a gantt chart.
    - Padraic Doyle
"""

import sys
import re
import glob
import datetime
import operator

MAX_DELAY = 60      # Maximum delay before a phase starts. Otherwise warn user.


def get_metrics_records(metrics_file_path):
    """
    Get the metrics records from the metrics file.
    """
    metrics_records = []
    with open(glob.glob(metrics_file_path)[0], 'r') as metrics_file:
        for line in metrics_file:
            metrics_records.append(line)
        metrics_file.close()
    return metrics_records


def get_plans(metrics_records):
    """
    Get a list of plans containing a list of phases.
    """
    first_time_stamp = metrics_records[0].split(',')[0]
    start_time = datetime.datetime.strptime(first_time_stamp,
        '%Y-%m-%d %H:%M:%S.%f')

    # Create a list of dictionaries containing Phase data.
    plans = []
    phase_records = []
    regexp = ('(.*?),(\\[LITP\\]\\[PLAN\\]\\[Run\\]\\[Phase)(\\d+)]' +
              '\\.TimeTaken=(\\d*\\.\\d+)(?![-+0-9\\.])')
    reg = re.compile(regexp, re.IGNORECASE | re.DOTALL)
    for record in metrics_records:
        match = reg.search(record)
        if match:
            phase = int(match.group(3))
            if (phase == 1) and phase_records:              # NEW PLAN
                last_plan_length = len(phase_records)
                if last_plan_length < 5:
                    print ("Discarding plan with {0} phases."
                        .format(last_plan_length))
                else:
                    plans.append(sorted(phase_records,
                                        key=operator.itemgetter('Phase')))
                phase_records = []

            phase_record = {}
            phase_record["Phase"] = int(match.group(3))
            date_time = datetime.datetime.strptime(match.group(1),
                                                 '%Y-%m-%d %H:%M:%S.%f')

            time_stamp = (date_time - start_time).seconds

            phase_record["Start"] = time_stamp
            phase_record["Duration"] = float(match.group(4))
            phase_record["Start"] = (phase_record["Start"] -
                phase_record["Duration"])
            phase_record["SquareBracketFields"] = match.group(2)
            phase_records.append(phase_record)
    plans.append(sorted(phase_records, key=operator.itemgetter('Phase')))
    return plans


def check_deltas(phase_records):
    """
    Report if time between phases seems excessive.
    """
    # Warn on unexpected deltas.
    for first, second in zip(phase_records, phase_records[1:]):
        delay = second['Start'] - first['Start']
        delay = ((second["Start"] - phase_records[0]["Start"]) -
                (first["Start"] - phase_records[0]["Start"] +
                    first["Duration"]))

        if delay > MAX_DELAY:
            print("WARNING: There was a {0:0.2f} second delay before Phase {1}"
                .format(delay, second['Phase']))


def get_phase_records(phase_records):
    """
    Get phase data for printing from phase_records.
    """
    file_records = []
    for phase in phase_records:
        file_record = ("{0}\t{1}\t{2}\t{3}\n".format(
            phase["Phase"],
            phase["Start"] - phase_records[0]["Start"],
            phase["Start"] - phase_records[0]["Start"] + phase["Duration"],
            phase["Duration"]))
        file_records.append(file_record)
    return file_records


def write_file(records, output_filename):
    """
    Write file.
    """
    # Write data to a file.
    with open(output_filename, "w") as output_file:
        for record in records:
            output_file.write(record)
        output_file.close()


def get_plot_cfg(phase_records):
    """
    Generate Gnuplot config lines from phase data.
    """
    plot_config = get_plot_headers(phase_records)
    plot_config = append_plot_objects(phase_records, plot_config)
    plot_config = append_plot_titles(phase_records, plot_config)
    return plot_config


def get_plot_headers(phase_records):
    """
    Generate Gnuplot config file headers from phase data.
    """

    plot_config = []
    rec_height = 0.8

    max_x_range = max([x['Start'] for x in phase_records])
    xaxis_range = "set xrange [0.000000:{0}]\n".format(max_x_range)
    plot_config.append(xaxis_range)

    yrange = "set yrange [{0}:{1}]\n".format(rec_height / 2,
        len(phase_records) + 1 - (rec_height / 2))
    plot_config.append(yrange)

    plot_config.append("set autoscale x\n")
    plot_config.append("set xlabel \"Time in seconds\"\n")
    plot_config.append("set ylabel \"Phases\"\n")
    plot_config.append("set title \"Gantt chart of Plan phases\"\n")

    phases = [x['Phase'] for x in phase_records]

    tics = ""
    for idx, phase in enumerate(reversed(phases), 1):
        tics += ' "{0}" {1},'.format(phase, idx)
    plot_config.append("set ytics ( {0} )\n".format(tics[:-1]))
    plot_config.append("set key outside width +2\n")
    plot_config.append("set grid xtics\n")
    plot_config.append("set palette model RGB defined (0 1.0 0.8 0.8, 1 1.0 " +
        "0.8 1.0, 2 .8 .8 1.0, 3 0.8 1.0 1.0, 4 0.8 1.0 0.8, 5 1.0 1.0 0.8)\n")
    plot_config.append("unset colorbox\n")

    return plot_config


def append_plot_objects(phase_records, plot_config):
    """
    Append lines for Gnuplot config objects from phase data.
    """
    phases = [x['Phase'] for x in phase_records]
    # Generate phase index for ypos
    for idx, phase in enumerate(phase_records):
        phase["ypos"] = len(phases) - idx
    frac = 0.0
    for idx, phase in enumerate(phase_records, 1):
        frac += (1.0 / len(phase_records))
        phase["Frac"] = frac

        plan_start = phase_records[0]["Start"]
        bottomleft_x = phase['Start'] - plan_start
        bottomleft_y = phase["ypos"] - 0.4
        topright_x = phase['Start'] - plan_start + phase["Duration"]
        topright_y = phase["ypos"] + 0.4

        obj_line_1 = ("set object {0} rectangle from {1}, {2} to {3}, {4} "
            .format(idx, bottomleft_x, bottomleft_y,
                    topright_x, topright_y))

        obj_line_2 = ("fillcolor palette frac {0:0.3f} fillstyle solid 0.8\n"
            .format(phase["Frac"]))
        plot_config.append(obj_line_1 + obj_line_2)
    return plot_config


def append_plot_titles(phase_records, plot_config):
    """
    Append lines for Gnuplot titles from phase data.
    """
    plot_config.append("plot \\\n")
    for phase in phase_records:
        plot_line_1 = ("\t-1 notitle \"{0}\" with lines linecolor "
            .format(phase["Phase"]))
        plot_line_2 = ("palette frac {0:0.2} linewidth 6, \\\n"
            .format(phase["Frac"]))
        plot_config.append(plot_line_1 + plot_line_2)
    return plot_config


def new_main(args):
    """ Main function.  """
    if len(args) == 1:
        print "\n\tUSAGE: {0} <metrics-log>\n".format(args[0])
        sys.exit(0)
    metrics_file_path = args[1]
    metrics_records = get_metrics_records(metrics_file_path)

    # Get a list if plans contained in the metrics file.
    plans_list = get_plans(metrics_records)
    for idx, plan in enumerate(plans_list, 1):
        # Check for gaps between plan phases and report to stdout.
        check_deltas(plan)

        # Get phases records in printable .csv form and write to file.
        phase_info = get_phase_records(plan)
        write_file(phase_info, 'plan_{0}_phases.dat'.format(idx))

        # Generate a Gnuplot config file from phase data.
        plot_cfg = get_plot_cfg(plan)
        plot_cfg[-1] = plot_cfg[-1][0:-4]
        write_file(plot_cfg, 'plan_{0}_plot.cfg'.format(idx))

if __name__ == '__main__':
    new_main(sys.argv)
