import os
import sys
import re

import os, sys, re

def prompt():
    # get PS1 or give it default
    return os.getcwd() + " "

def execute_cmd(cmd):
    # get the process id
    pid = os.fork()
    # get the process id, check if it is a cmd
    if pid == 0:
        try:
            os.execve(cmd[0], cmd, os.environ)
        except FileNotFoundError:
            sys.stderr.write(f"{cmd[0]}: cmd not found\n")
            sys.exit(1)
    else:
        # get exit code and write to terminal
        _, exit_code = os.waitpid(pid, 0)

        if exit_code != 0:
            sys.stderr.write(f"Program terminated with exit code {exit_code}\n")
            sys.exit()

def change_directory(args):
    try:
       pwd = os.chdir(args[0])
       prompt(pwd)
    except:
        sys.stderr.write(f"{args[0]}: No such file or directory\n")

def list_directory():
    dirs = os.listdir('.')
    sys.stdout.write("\n".join(dirs) + "\n")      

def execute_pipeline(pipeline):
    # creating a list append cmds to said list
    pipe_fds = []
    for i in range(len(pipeline)):
        r, w = os.pipe()
        pipe_fds.append(r)
        pipe_fds.append(w)
        # check if current process is a child process
        if os.fork() == 0:
            # if it is a child process
            if i != 0:
                # duplicate the read-end of the pipe to the stdin file descriptor
                os.dup2(pipe_fds[i*2-2], sys.stdin.fileno())
            # if it is not the index of the last cmd
            if i != len(pipeline) - 1:
                # redirect the output of the current cmd to the write end of the pipe
                # connecting the input of hte next cmd in the pipeline
                os.dup2(pipe_fds[i*2+1], sys.stdout.fileno())
            # close all file descriptors
            for fd in pipe_fds:
                os.close(fd)
            # pass the current pipeline cmd to execute_cmd function
            execute_cmd(pipeline[i])
    # close file descriptors
    for fd in pipe_fds:
        os.close(fd)
    # wait on child
    for i in range(len(pipeline)):
        os.wait()

def execute_background_task(cmd):
    pid = os.fork()
    # taking the child process and giving it process group leader
    if pid == 0:
        os.setsid()
        # allows full perms to child
        os.umask(0)
        # error handling
        try:
            # attempts to execute
            os.execve(cmd[0], cmd, os.environ)
        except FileNotFoundError:
            # doesn't work write error message
            sys.stderr.write(f"{cmd[0]}: cmd not found\n")
            sys.exit(1)
    else:
        # if the process started properly give process ID
        sys.stdout.write(f"[{pid}]")

def parse_cmd(cmd):
    # this sets up the pipeline for multiple commands
    pipeline = re.split(r'\s*\|\s*', cmd)
    # if it has more than one command then execute commands as
    # seperated by | symbol.
    if len(pipeline) > 1:
        pipeline = [re.split(r'\s+', x) for x in pipeline]
        execute_pipeline(pipeline)
    else:
        # splits command to allow for whitespace
        cmd = re.split(r'\s+', pipeline[0])
        # change directory
        if cmd[0] == "cd":
            change_directory(cmd[1:])
        # list current subdirectories
        elif cmd[0] == "ls":
            list_directory()
        # exit shell
        elif cmd[0] == "exit":
            sys.exit(0)
        elif cmd[-1] == "&":
            execute_background_task(cmd[:-1])
        else:
            execute_cmd(cmd)

while True:
    sys.stdout.write(prompt())
    sys.stdout.flush()

    cmd = ''
    while True:
        char = sys.stdin.read(1)
        if not char or char == '\n':
            break
        cmd += char

    parse_cmd(cmd)


