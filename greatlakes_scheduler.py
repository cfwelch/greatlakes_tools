

import datetime, subprocess, inspect, time, sys, os, re

from collections import defaultdict
from argparse import ArgumentParser

FNULL = open(os.devnull, 'w')
DIR_PATH = '.'

def main():
    parser = ArgumentParser()
    parser.add_argument('-mg', '--max-gpus', dest='max_gpus', help='Max GPUs allowed for the account.', default=5, type=int)
    parser.add_argument('-lf', '--leave-free', dest='leave_free', help='Number of GPUs to leave free.', default=1, type=int)
    parser.add_argument('-a', '--account', dest='account', help='Greatlakes account to use.', default='mihalcea1', type=str)
    parser.add_argument('-pf', '--param-file', dest='param_file', help='File containing parameters to run.', default='params', type=str)
    args = parser.parse_args()

    param_set = []
    with open(args.param_file) as handle:
        for line in handle.readlines():
            tline = line.strip()
            if tline[0] == '#':
                continue
            param_set.append(tline)

    cumulative_wait = 0
    while len(param_set) > 0:
        # find an available GPU
        num_usable = get_avail_gpu(args)
        cprint('Number of usable: ' + str(num_usable))
        # if GPU available pop a job
        if num_usable > 0:
            cumulative_wait = 0
            next_p = param_set.pop()
            runstr = next_p
            cwd = '.'
            cprint('Running \'' + runstr + '\'...')
            cprint('There are ' + str(len(param_set)) + ' jobs remaining...')
            proc = subprocess.Popen(runstr, cwd=cwd, stdout=FNULL, shell=True)
            if len(param_set) > 0:
                time.sleep(60) # wait for squeue to update
        else:
            # wait for GPU to become available
            time.sleep(60*5)
            cumulative_wait += 60*5
            cprint('Scheduler has been waiting for a GPU for ' + str(cumulative_wait) + ' seconds...')
    cprint('All jobs have been scheduled!\n')

def get_avail_gpu(args):
    out = subprocess.check_output(['squeue', '-A', args.account])
    out = [i.strip() for i in out.decode().split('\n') if not i.strip().startswith('JOBID') and i.strip() != '']

    job_states = defaultdict(lambda: 0)

    for line in out:
        t = re.sub('\s+', '\t', line).split('\t')
        part = t[1]
        status = t[5]
        if part == 'gpu':
            job_states[status] += 1
            # print(t)

    # print('GPU Job States:')
    # for k,v in job_states.items():
    #     print('\t' + k + ': ' + str(v))

    # if you don't care about job state
    # total_jobs = sum(job_states.values())
    # print('Total Jobs: ' + str(total_jobs))
    total_jobs = job_states['PD'] + job_states['R']

    return args.max_gpus - args.leave_free - total_jobs

def cprint(msg, logname='scheduler', error=False, important=False, ptime=True, p2c=True):
    # tmsg = msg if not important else colored(msg, 'cyan')
    # tmsg = tmsg if not error else colored(msg, 'red')
    tmsg = msg
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    cmsg = str(st) + ': ' + str(tmsg) if ptime else str(tmsg)
    tmsg = str(st) + ': ' + str(msg) if ptime else str(msg)
    if p2c:
        print(cmsg)
    log_file = open(DIR_PATH + '/' + logname + '.log', 'a')
    log_file.write(tmsg + '\n')
    log_file.flush()
    log_file.close()

if __name__ == '__main__':
    main()
