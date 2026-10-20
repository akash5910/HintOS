"""Short descriptions used to match a question to a syllabus topic."""

TOPIC_PROFILES = {
    "OS introduction and structure": (
        "purpose, functions, services and design goals of operating systems; "+
        "monolithic, layered, modular, microkernel designs; abstractions and resource management; "+
        "security, networking, multimedia"
    ),
    "OS principles and system calls": (
        "system calls and application programming interfaces; user mode and kernel mode; "+
        "protection, traps, interrupts, exception handling, kernel entry"
    ),
    "Banker's Algorithm": (
        "Banker's algorithm for resource allocation and deadlock avoidance; Need matrix, maximum claim, "+
        "allocated resources, available resources, safe state and safe sequence"
    ),
    "processes and threads": (
        "process control block PCB, process states, ready queue, context switch, process creation; "+
        "Unix fork exec wait; user threads, kernel threads and thread models"
    ),
    "CPU scheduling": (
        "preemptive and nonpreemptive CPU scheduling; FCFS, first come first served, SJF, "+
        "shortest job first, shortest remaining time first, priority scheduling, round robin, "+
        "multilevel queue, multilevel feedback queue, multiprocessor scheduling; waiting turnaround response time"
    ),
    "deadlocks": (
        "deadlock conditions, resource allocation graph, detection, prevention, avoidance, "+
        "recovery and handling deadlocked processes"
    ),
    "concurrency and IPC": (
        "synchronization, mutual exclusion, mutex, spinlock, semaphore, critical section, race condition, "+
        "monitors, condition variables, dining philosophers, Unix IPC, scalable locks, lock-free coordination"
    ),
    "memory management": (
        "main memory allocation, contiguous allocation, first fit best fit worst fit, fragmentation, "+
        "paging, segmentation, address translation, virtual memory, page tables, TLB"
    ),
    "page replacement and thrashing": (
        "demand paging, page fault handling, FIFO LRU clock page replacement, reference strings, "+
        "thrashing, working set model, frame allocation"
    ),
    "virtualization": (
        "virtual machines, virtual machine monitor, hypervisor type one type two, "+
        "hardware virtualization, containers, container isolation, virtualization overhead and cost"
    ),
    "file systems": (
        "file system interface, file operations, directories, inodes, file metadata, "+
        "file-system implementation, allocation, free space, recovery, journaling, soft updates, "+
        "log structured file systems and distributed file systems"
    ),
    "storage and disk scheduling": (
        "disk structure, hard drives, solid state drives, storage attachment, RAID, "+
        "disk scheduling SSTF SCAN C-SCAN, seek time and head movement"
    ),
    "security and protection": (
        "system threats, malware, viruses, worms, security policy and mechanism, "+
        "authentication and authorization, protection domains, access matrix, ACLs, capabilities"
    ),
    "performance and mobile systems": (
        "operating system performance, bottlenecks, scaling, multiprocessor performance, "+
        "mobile operating systems and future directions"
    ),
}
