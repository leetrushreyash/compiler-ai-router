"""Sample code demonstrating command injection vulnerabilities."""

import os
import subprocess


def execute_user_command(user_input):
    """Vulnerable command execution - command injection."""
    os.system(f"echo {user_input}")


def ping_host(hostname):
    """Vulnerable ping - command injection."""
    result = subprocess.run(f"ping -c 1 {hostname}", shell=True)
    return result


def process_file(filename):
    """Vulnerable file processing - command injection."""
    os.system(f"cat {filename} | grep pattern")


def search_logs(search_term):
    """Vulnerable log search - command injection."""
    os.system(f"grep {search_term} /var/log/app.log")


def convert_image(source, dest):
    """Vulnerable image conversion - command injection."""
    cmd = f"convert {source} {dest}"
    os.system(cmd)
