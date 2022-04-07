
from email.mime.text import MIMEText
import platform
import smtplib

import psutils.scheduler as psu_sched
from psutils.shell import run_subprocess


def send_email(to_addr, subject, body, from_addr=None):
    if from_addr is None:
        platform_node = platform.node()
        from_addr = platform_node if platform_node is not None else 'your-computer'
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    s = smtplib.SMTP('localhost')
    s.sendmail(to_addr, [to_addr], msg.as_string())
    s.quit()


def send_email_shell_mail(to_addr, subject, body):
    mail_cmd = """ echo "{}" | mail -s "{}" {} """.format(body, subject, to_addr)
    run_subprocess(mail_cmd)


def send_script_completion_email(args, error_trace):
    email_body = args.script_run_cmd+'\n'
    if error_trace is not None:
        email_status = "ERROR"
        email_body += "\n{}\n".format(error_trace)
    else:
        email_status = "COMPLETE"
    email_subj = "{} - {}".format(email_status, args.script_fname)
    send_email(args.get(psu_sched.ARGSTR_EMAIL), email_subj, email_body)
