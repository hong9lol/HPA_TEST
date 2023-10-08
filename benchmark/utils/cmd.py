import subprocess


def execute_cmd(cmd):
    return subprocess.check_output(cmd, shell=True, universal_newlines=True)
