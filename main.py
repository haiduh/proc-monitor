import time
import os
import sys
from collections import namedtuple

CPUStats = namedtuple("CPUStats", ["user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal", "guest", "guest_nice"])

def read_cpu_stats():
    with open("/proc/stat") as f: # This reads the proc stat and put it into a file
        line = f.readline()
    
    cpu_stats = map(int, line.split()[1:]) # Maps each string into a integer and u can add [] arguments after line.split because it becomes a string
    
    return CPUStats(*cpu_stats) # * turns it from a singular argument into positional ones

stats1 = read_cpu_stats()
stats2 = read_cpu_stats()

# print("This is stats1: ", stats1)
# print("This is stats2: ", stats2)
# print(stats1.user - stats2.user)

def calculate_cpu_percent(snap1, snap2):
    user_delta = snap2.user - snap1.user
    nice_delta = snap2.nice - snap1.nice
    system_delta = snap2.system  - snap1.system
    irq_delta  = snap2.irq - snap1.irq
    softirq_delta = snap2.softirq - snap1.softirq
    iowait_delta = snap2.iowait - snap1.iowait
    active_delta = user_delta + nice_delta + system_delta + irq_delta + softirq_delta + iowait_delta
    total_delta = sum(snap2) - sum(snap1)
    
    if total_delta == 0:
        return 0.0
    
    cpu_percent = (active_delta/total_delta) * 100
    
    return round(cpu_percent, 3)

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
    usage_percent = (used / mem_total) * 100
    
    return round(usage_percent, 3)

while True:
    stats1 = stats2
    time.sleep(3)
    stats2 = read_cpu_stats()
    total_stats = calculate_cpu_percent(stats1, stats2)
    total_memory = calculate_mem_percent(read_mem_stats())
    print(f"{total_stats}%")
    print(f"{total_memory}%")
