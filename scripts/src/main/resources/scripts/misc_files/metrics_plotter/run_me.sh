#!/bin/bash

###############################################################################
#
#  This is a tool to examine the ENM metrics log, report on excessive gaps 
#   between plan phases, and graph the plan in a gantt chart. 
#  The metrics log is located on the MS at '/var/log/litp/metrics.log'
#   - Padraic Doyle
#
###############################################################################


# Remove old data files if they exist from previous run.
  rm -f plan_*_phases.dat  plan_*_plot.cfg  gantt_phases.png 

# Generate Phase metrics data file (phases.dat) and Gnuplot config file 'plan_1_plot.cfg' from metrics log.
 ./parse_metrics.py  metrics.log


# Check if gnuplot installed.
command -v gnuplot -V >/dev/null 2>&1 || { echo -e >&2 "\n\tError: Need gnuplot\n\n\tTry: sudo yum install -y gnuplot\n"; exit 1; }

# Check for graphics package: libpng-devel 
rpm -qa | grep -qw libpng-devel || { echo -e "\n\tError: Need libpng-devel \n\n\tTry: sudo yum -y install libpng-devel\n" ; exit 1; }

# Plot the phase data
gnuplot -e "set terminal png size 1920,1028 ; set output 'gantt_phases.png' "  plan_1_plot.cfg >/dev/null 2>&1

# Or use prettier RHEL 7 plotting. Doesn't work with RHEL 6
#gnuplot -e "set terminal pngcairo size 1920,1028 font 'Verdana,8'; set output 'gantt_phases.png' "  plan_1_plot.cfg

# Display the gantt chart with suitable graphics viewer.
 eog gantt_phases.png &

