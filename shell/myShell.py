import os, sys, re

def prompt():
    # get PS1 or give it default
    path = os.getcwd()
    os.environ["PS1"] = f"myshell:{path}$ "
    return os.environ.get('PS1')

def execute_cmd(cmd):
    # get the process id
    pid = os.fork()
    # get the process id, check if it is a cmd
    if pid == 0:
        if '>' in cmd:
            idx = cmd.index('>')
            fd_out = os.open(cmd[idx + 1], os.O_CREAT | os.O_WRONLY)
            os.dup2(fd_out, sys.stdout.fileno())
            cmd = cmd[:idx]
        if '<' in cmd:
            idx = cmd.index('<')
            fd_in = os.open(cmd[idx + 1], os.O_RDONLY)
            os.dup2(fd_in, sys.stdin.fileno())
            cmd = cmd[:idx]
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
    # takes us to home directory
    if not args:
        os.chdir(os.path.expanduser("~"))
        return
    # takes us to parent directory
    cwd = os.getcwd()
    if args[0] == "..":
        os.chdir(os.path.abspath(os.path.join(cwd, os.pardir)))
    else:
        try:
            path = " ".join(args)
            os.chdir(path)
        except:
            sys.stderr.write(f"{path}: No such file or directory\n")

def list_directory():
    # get current directory and then get it's paths
    cwd = os.getcwd()
    paths = os.listdir(cwd)
    # create two lists that hold the directories in that path and files
    # exclude the hidden ones
    dirs = [d for d in paths if os.path.isdir(os.path.join(cwd, d)) and not d.startswith(".")]
    files = [f for f in paths if os.path.isfile(os.path.join(cwd, f)) and not f.startswith(".")]
    count = 0
    # iterate through the dirs list and print six to a line
    for d in dirs:
        if count == 6:
            sys.stdout.write("\n")
            count = 0
        sys.stdout.write(f"{d} ")
        count+=1
    if count > 0:
        sys.stdout.write("\n")
    # iterate through the files list and print six to a line
    for f in files:
        if count == 6:
            sys.stdout.write("\n")
            count = 0
        sys.stdout.write(f"{f} ")
        count+=1
    if count > 0:
        sys.stdout.write("\n")


def execute_pipeline(pipeline):
    # Create a pipe for each command in the pipeline
    pipes = [os.pipe() for _ in range(len(pipeline) - 1)]
    
    # Create child processes for each command in the pipeline
    pids = []
    for i, cmd in enumerate(pipeline):
        pid = os.fork()
        if pid == 0:
            # If this is not the first command, redirect stdin to the read end of the previous pipe
            if i > 0:
                os.dup2(pipes[i - 1][0], 0)
            
            # If this is not the last command, redirect stdout to the write end of the next pipe
            if i < len(pipeline) - 1:
                os.dup2(pipes[i][1], 1)
            
            # Close all file descriptors
            for p in pipes:
                os.close(p[0])
                os.close(p[1])
            
            # Execute the command
            os.execvp(cmd[0], cmd)
        
        pids.append(pid)
    
    # Close all file descriptors
    for p in pipes:
        os.close(p[0])
        os.close(p[1])
    
    # Wait for all child processes to finish
    for pid in pids:
        os.waitpid(pid, 0)    

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


