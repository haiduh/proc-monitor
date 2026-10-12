import time
import os
from datetime import datetime
from collections import namedtuple

CPUStats = namedtuple("CPUStats", ["user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal", "guest", "guest_nice"])
ProcessStats = namedtuple("ProcessStats", ["pid", "process_name", "utime", "stime"])
CPU_THRESHOLD = 80
MEM_THRESHOLD = 80

def read_cpu_stats():
    with open("/proc/stat") as f: # This reads the proc stat and put it into a file
        line = f.readline()
    cpu_stats = map(int, line.split()[1:]) # Maps each string into an integer, [1:] skips the "cpu" label
    return CPUStats(*cpu_stats) # * turns it from a singular argument into positional ones

def calculate_cpu_percent(snap1, snap2):
    user_delta = snap2.user - snap1.user
    nice_delta = snap2.nice - snap1.nice
    system_delta = snap2.system - snap1.system
    irq_delta = snap2.irq - snap1.irq
    softirq_delta = snap2.softirq - snap1.softirq
    iowait_delta = snap2.iowait - snap1.iowait
    active_delta = user_delta + nice_delta + system_delta + irq_delta + softirq_delta + iowait_delta
    total_delta = sum(snap2) - sum(snap1)
    if total_delta == 0:
        return 0.0
    return round((active_delta / total_delta) * 100, 3)

def read_mem_stats():
    mem = {}
    with open("/proc/meminfo") as f:
        for line in f:
            (key, val, *_) = line.split() # *_ is so that if there are 3 or more values, we throw them away
            mem[key.strip(":")] = int(val)
    return mem

def calculate_mem_percent(memory):
    mem_total = memory["MemTotal"]
    mem_available = memory["MemAvailable"]
    used = mem_total - mem_available
    return round((used / mem_total) * 100, 3)

def read_processes_stats(pid):
    try:
        with open(f"/proc/{pid}/stat") as f:
            line = f.read()
        last_paren = line.rfind(")")   # Find the character of the parentheses
        name_part = line[:last_paren]  # gets the name for everything before the parentheses, e.g 2282 (Web Content
        rest = line[last_paren+1:]     # stores the rest after the parentheses
        pid = name_part.split("(")[0].strip()  # would be 172 for PID 172
        name = name_part.split("(")[1]   # everything after the opening paren
        fields = rest.split()
        utime = int(fields[11])
        stime = int(fields[12])
        return ProcessStats(pid, name, utime, stime)
    except FileNotFoundError:
        return None

def get_all_processes():
    proc_stats = []
    pids = [entry for entry in os.listdir("/proc") if entry.isnumeric()]
    for pid in pids:
        procs = read_processes_stats(pid)
        if procs is not None:
            proc_stats.append(procs)
    return proc_stats

def calculate_process_cpu(snapshot1, snapshot2, total_cpu_delta):
    snap1_by_pid = {proc.pid: proc for proc in snapshot1}
    snap2_by_pid = {proc.pid: proc for proc in snapshot2}
    total_procs = []
    for i in snap2_by_pid:
        if i in snap1_by_pid:
            pid1 = snap1_by_pid[i]
            pid2 = snap2_by_pid[i]
            name = pid1.process_name
            process_delta = (pid2.utime + pid2.stime) - (pid1.utime + pid1.stime)
            process_cpu_percent = round((process_delta / total_cpu_delta) * 100, 3)
            total_procs.append((i, name, process_cpu_percent))
    return sorted(total_procs, key=lambda x: x[2], reverse=True)[:10]

def colourise(value, low_threshold, high_threshold):
    if value >= high_threshold:
        code = "\033[91m"  # bright red
    elif value >= low_threshold:
        code = "\033[93m"  # bright yellow
    else:
        code = "\033[92m"  # bright green
    return f"{code}{value:.1f}%\033[0m"

def check_alerts(cpu_percent, mem_percent):
    RED = "\033[91m"
    RESET = "\033[0m"
    if cpu_percent > CPU_THRESHOLD:
        print(f"{RED}⚠ CPU USAGE TOO HIGH: {cpu_percent:.1f}%{RESET}\n")
    if mem_percent > MEM_THRESHOLD:
        print(f"{RED}⚠ MEMORY USAGE TOO HIGH: {mem_percent:.1f}%{RESET}\n")

def display_proc(cpu_percent, mem_percent, top_procs):
    now = datetime.now().strftime("%H:%M:%S")
    print(f"proc-monitor | Last updated: {now}\n")
    print(f"CPU: {colourise(cpu_percent, 40, CPU_THRESHOLD)}")
    print(f"Memory: {colourise(mem_percent, 40, MEM_THRESHOLD)}\n")
    check_alerts(cpu_percent, mem_percent)
    print(f"{'PID':<8} {'NAME':<20} {'CPU%':>8}")
    print("-" * 38)
    for proc in top_procs:
        print(f"{proc[0]:<8} {proc[1]:<20} {proc[2]:>8.2f}%")

stats1 = read_cpu_stats()
procs1 = get_all_processes()

while True:
    time.sleep(3)
    stats2 = read_cpu_stats()
    procs2 = get_all_processes()
    total_cpu_delta = sum(stats2) - sum(stats1)
    total_cpu = calculate_cpu_percent(stats1, stats2)
    total_memory = calculate_mem_percent(read_mem_stats())
    top_procs = calculate_process_cpu(procs1, procs2, total_cpu_delta)
    stats1 = stats2
    procs1 = procs2
    os.system("clear")
    display_proc(total_cpu, total_memory, top_procs)