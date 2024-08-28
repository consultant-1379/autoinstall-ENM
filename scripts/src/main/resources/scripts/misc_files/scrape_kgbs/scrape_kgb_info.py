#!/usr/bin/python
"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     July 2017
@author:    Laura Forbes

This script is used to retrieve the results of the last run KGBs in a given list and optionally send an email report.

N.B. To run this script, you must have the Python module beautifulsoup4 (bs4) installed on your local machine:
    sudo pip install beautifulsoup4
For more info on Beautiful Soup, visit: https://www.crummy.com/software/BeautifulSoup/

Usage:
Run the script passing in a text file with the list of KGBs that you want
    to check. There should be one KGB per line and in the following format:
    kgb_name,kgb_job_name,package_name
    Ex. expansion,ERIClitpcore_Expansion_KGB,ERIClitpcore_CXP9030418

python scrape_kgb_info.py <kgbs_to_check.txt>

If you want to send an email report, also pass in a text file of the following
    format (note that there must be a space on either side of each equals sign):
    RECIPIENT_LIST = first.last@ammeon.com,team@ammeon.com,important.person@ammeon.com
    EMAIL_SUBJECT = Something Interesting
    SEND_FROM = youremail@ammeon.com
    MAIL_PASSWD = your_gmail_password

python scrape_kgb_info.py <kgbs_to_check.txt> <email_info.txt>
"""
import sys
import requests
from bs4 import BeautifulSoup
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime

# Count number of successful, failed and running KGBs
num_succ, num_fail, num_running = 0, 0, 0

jenkins_url = "https://fem112-eiffel004.lmera.ericsson.se:8443/jenkins"
last_build_console = "{0}/job/{1}/lastBuild/consoleFull"
progressive_output = "{0}/job/{1}/{2}/logText/progressiveHtml?start=0"
job_report_url = "{0}/job/{1}/{2}/artifact/test-results/ERICTAFlitp{3}-results/test_report.html"


def scrape_page(kgb_name, pkg_name):
    """
    Description:
        Find the last Jenkins run (or currently running) job of the given KGB and return the
        build number, package version used, whether the job was successful (or still in
        progress) and the time the build started.
    Args:
        kgb_name (str): Name of KGB
        pkg_name (str): Package name of KGB, ex. ERIClitpcore_CXP9030418
    Returns:
        build_num (str): Job number of last run job or job currently in progress
        package_version (str): Version of KGB test package
        build_res (str): Result of the job. "SUCCESS", "FAILURE" or None if job is still running
        start_time (str): (Swedish) Time of when the build was triggered
    """
    global num_succ, num_fail, num_running

    # Link to last build of the given job
    last_build_job = last_build_console.format(jenkins_url, kgb_name)
    # Get contents of link
    last_build_page = requests.get(last_build_job)
    soup = BeautifulSoup(last_build_page.content, 'html.parser')
    # print(soup.prettify())
    # Build number should be in Job Title
    page_title = soup.find('title').get_text()
    build_num = page_title.split('#')[1].split()[0]

    # If job is still running (assume it is), need to get Progressive Output
    progressive_page = progressive_output.format(jenkins_url, kgb_name, build_num)
    last_build_page = requests.get(progressive_page)
    soup = BeautifulSoup(last_build_page.content, 'html.parser')

    # Find the testware package version
    find_ver = 'Updating rpm for:  {0}-'.format(pkg_name)
    package_version = soup.find_all(string=re.compile('.*{0}.*'.format(find_ver)), recursive=True)
    if package_version:
        package_version = package_version[0].split('-')[-1].split('.rpm')[0]
    else:
        package_version = "Package Version Not Found"

    # Check whether the job passed, failed or is still running
    finished = 'Finished: '
    build_res = soup.find_all(string=re.compile('.*{0}.*'.format(finished)), recursive=True)
    if build_res:
        build_res = build_res[0].split()[-1]
        if "SUCCESS" in build_res:
            num_succ += 1
        else:
            num_fail += 1
    else:
        build_res = None
        num_running += 1

    # Find build start time
    find_start_time = soup.findAll("span", {"class": "timestamp"})[0]  # SWEDISH TIME
    start_time = []
    for char in find_start_time:
        start_time.append((str(char)))
    start_time = start_time[0].split('<b>')[1].split('</b>')[0]

    return build_num, package_version, build_res, start_time


def construct_email_kgb_info(kgb_name, pkg_name, version, start_time, result, link):
    """
    Description:
        Transforms KGB info into HTML.
    Args:
        kgb_name (str): Name of KGB
        pkg_name (str): Package name of KGB, ex. ERIClitpcore_CXP9030418
        version (str): Version of KGB test package
        start_time (str): Time the build started
        result (str): Whether job passed, failed or is still running. Must be one of: "SUCCESS", "FAILURE", None
        link (str): Link to test report or console output, if job is still running
    Returns:
        kgb_info (str): KGB info formatted into HTML
    """
    global num_succ, num_fail, num_running

    colour = "blue"
    if result == "SUCCESS":
        colour = "green"
    elif result == "FAILURE":
        colour = "red"

    kgb_info = '<p><u><b>{0}</b></u><br>'.format(kgb_name.upper())

    kgb_info += "{0}&emsp;&emsp;{1}<br>".format(pkg_name, version)
    #kgb_info += "Build start time:&emsp;{0}<br>".format(start_time)
    if result == "SUCCESS" or result == "FAILURE":
        kgb_info += '<a href="{0}">Test Report</a>&emsp;<font color="{1}">{2}</font><br>'.format(link, colour, result)
    else:
        kgb_info +=\
            '<a href="{0}">Console Output</a>&emsp;<font color="{1}">STILL RUNNING</font><br>'.format(link, colour)

    kgb_info += "</p>"
    return kgb_info


def send_email(email_body, send_details_file):
    """
    Description:
        Sends KGB Report email with the given message and details specified in the passed file.
        More info on the file in the description at the top of this script.
    Args:
        email_body (str): Message to send in HTML format
        send_details_file (str): File containing recipient list,
            email subject, gmail address to send from and gmail password
    """
    recipient_list = None
    email_subject = "KGB Report"
    mail_user = None
    mail_passwd = None
    with open(send_details_file) as infile:
        for line in infile:
            if 'RECIPIENT_LIST' in line:
                recipient_list = line.split(" = ")[1].rstrip().split(",")
            elif 'EMAIL_SUBJECT' in line:
                email_subject = line.split(" = ")[1].rstrip()
            elif 'SEND_FROM' in line:
                mail_user = line.split(" = ")[1].rstrip()
            elif 'MAIL_PASSWD' in line:
                mail_passwd = line.split(" = ")[1].rstrip()

    date_today = datetime.datetime.now().strftime("%d %B %Y")
    email_subject += " {0} [Automated]".format(date_today)

    # First line in email will be stats info
    stats = '<font color="green">SUCCESSFUL: {0}</font>&emsp;'.format(num_succ)
    if num_fail > 0:
        colour = "red"
    else:
        colour = "green"
    stats += '<font color="{0}">FAILED: {1}</font>&emsp;'.format(colour, num_fail)
    if num_running > 0:
        colour = "blue"
    else:
        colour = "green"
    stats += '<font color="{0}">STILL RUNNING: {1}</font><br><br>'.format(colour, num_running)
    email_body = stats + email_body

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = email_subject
    msg['From'] = mail_user
    msg['To'] = ', '.join(recipient_list)
    # Create the body of the message (a plain-text and an HTML version).
    html = email_body

    # Record the MIME types - text/html.
    # Attach parts into message container.
    html_mime = MIMEText(html, 'html')
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(html_mime)
    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login(mail_user, mail_passwd)
    mail.sendmail(mail_user, recipient_list, msg.as_string())
    mail.quit()

# Read in the list of KGBs to check
kgb_file = sys.argv[1]
kgb_list = []
with open(kgb_file) as f:
    kgbs_to_check = f.readlines()
# Create a dictionary of the KGB jobs
for line in kgbs_to_check:
    k, jn, pn = line.rstrip().split(',')
    dict_format = {'KGB': k, 'job_name': jn, 'pkg_name': pn}
    kgb_list.append(dict_format)

# Only send email if parameter is passed in
email_report = False
if len(sys.argv) > 2:
    email_report = True
email_info = "<html><body>"

for kgb in kgb_list:
    # Get info of last build of the KGB
    build_num, pkg_ver, build_result, build_start_time = scrape_page(kgb['job_name'], kgb['pkg_name'])

    print "----------\n{0}\n----------".format(kgb['KGB'].upper())
    print "{0}\t\t{1}".format(kgb['pkg_name'], pkg_ver)
    print "Build start time:\t{0}".format(build_start_time)

    # Only link Test Report if job is finished running
    if not build_result:
        # Otherwise link the console output
        build_url = jenkins_url + "/job/{0}/{1}/consoleFull".format(kgb['job_name'], build_num)
        print "Job still running:\t{0}".format(build_url)
        email_link = build_url
    else:
        report_url = job_report_url.format(jenkins_url, kgb['job_name'], build_num,
                                           kgb['pkg_name'].split('ERIClitp')[1].split('_')[0])
        print "Test Report:\t{0}\t{1}".format(report_url, build_result)
        email_link = report_url

    email_info += construct_email_kgb_info(
        kgb['KGB'], kgb['pkg_name'], pkg_ver, build_start_time, build_result, email_link)

print "SUCCESSFUL: {0}\t\tFAILED: {1}\tSTILL RUNNING: {2}".format(num_succ, num_fail, num_running)

if email_report:
    email_info += "</body></html>"
    send_email(email_info, sys.argv[2])
