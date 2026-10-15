# Quiz evaluation

Generated 2026-10-15 by `eval/quiz_eval.py --n 5` (one quiz per unit, seed 0). Generator `openai/gpt-oss-120b`, judge `qwen/qwen3.8-27b`.

| metric | value |
|---|---|
| **valid questions** (target >= 95%) | **100.0%** (25/25) |
| answer supported by its cited slide | 96.0% (24/25 checked) |

| unit | generated | valid | calls | unsupported | rejected reasons |
|---|---|---|---|---|---|
| Unit 1 | 5 | 5 | 1 | 1 | - |
| Unit 2 | 5 | 5 | 1 | 0 | - |
| Unit 3 | 5 | 5 | 1 | 0 | - |
| Unit 4 | 5 | 5 | 1 | 0 | - |
| Unit 5 | 5 | 5 | 1 | 0 | - |

## Questions

- Unit 1 | What is the role of the kernel in an operating system? -> **It is the active part of the OS that can interact with hardware** (Unit 1_Part 1_Introduction & OS Structure, p.12; judge: supported)
- Unit 1 | Which of the following is NOT listed as a function of the Command Interpreter System? -> **Graphics rendering** (Unit 1_Part 1_Introduction & OS Structure, p.25; judge: supported)
- Unit 1 | Which type of Real‐Time Operating System guarantees that deadlines are never missed? -> **Hard Real‐Time OS** (Unit 1_Part 1_Introduction & OS Structure, p.37; judge: UNSUPPORTED)
- Unit 1 | According to the slide on Process vs Program, what distinguishes a process from a program? -> **A process is an active entity whereas a program is passive** (Unit 1_Part 2_ Process management, p.3; judge: supported)
- Unit 1 | In priority scheduling, when does the highest‐priority process have a waiting time of zero? -> **In preemptive mode regardless of arrival times** (Unit 1_Part 2_ Process management, p.83; judge: supported)
- Unit 2 | According to slide 1, what is a race condition? -> **When processes access shared data and the result depends on the order of execution** (Unit 2_Process Synchronization_Deadlock, p.5; judge: supported)
- Unit 2 | Based on slide 2, which operation actually decrements the semaphore value S? -> **WAIT (S)** (Unit 2_Process Synchronization_Deadlock, p.10; judge: supported)
- Unit 2 | From slide 5, which statement correctly describes the No‐Pre‐emptive condition? -> **Resources already allocated to a process cannot be pre‐empted** (Unit 2_Process Synchronization_Deadlock, p.26; judge: supported)
- Unit 2 | According to slide 7, what must a process do when it is denied a request for additional resources? -> **Release all currently held resources and possibly request them again later** (Unit 2_Process Synchronization_Deadlock, p.35; judge: supported)
- Unit 2 | In the resource‐allocation graph described on slide 8, how is a process represented? -> **Circle** (Unit 2_Process Synchronization_Deadlock, p.39; judge: supported)
- Unit 3 | What type of cache is described as extremely fast, relatively small, and usually embedded in the processor chip? -> **L1 cache** (Unit 3_Memory management, p.5; judge: supported)
- Unit 3 | Which of the following is an advantage of the single contiguous memory management scheme? -> **Simple to implement** (Unit 3_Memory management, p.9; judge: supported)
- Unit 3 | In dynamic partitioning, how are the sizes of partitions determined? -> **They are variable and depend on each process's needs** (Unit 3_Memory management, p.14; judge: supported)
- Unit 3 | Which allocation algorithm selects the largest available partition for each request? -> **Worst-fit** (Unit 3_Memory management, p.22; judge: supported)
- Unit 3 | How many bits are required for the frame number if the number of frames in main memory is 2^7? -> **7 bits** (Unit 3_Memory management, p.35; judge: supported)
- Unit 4 | Why are disk scheduling algorithms needed according to slide 1? -> **They minimize seek time by ordering requests** (Unit 4_Storage management_ Disk Schduling, p.3; judge: supported)
- Unit 4 | What is a cylinder in a magnetic disk as defined on slide 2? -> **A collection of all tracks at the same distance from the edge of the platter** (Unit 4_Storage management_ Disk Schduling, pp.5-6; judge: supported)
- Unit 4 | Which statement about the First Come First Serve (FCFS) disk scheduling algorithm is true according to slide 3? -> **It processes requests in the order they arrive** (Unit 4_Storage management_ Disk Schduling, pp.8-9; judge: supported)
- Unit 4 | What is a disadvantage of the SCAN disk scheduling algorithm mentioned on slide 7? -> **The head continues to the end even if no requests exist in that direction** (Unit 4_Storage management_ Disk Schduling, p.17; judge: supported)
- Unit 4 | According to slide 12, which advantage is associated with the C‐LOOK algorithm? -> **The waiting time is decreased** (Unit 4_Storage management_ Disk Schduling, p.26; judge: supported)
- Unit 5 | What does the Open(Fi) operation do according to the file operations slide? -> **Searches the directory structure on disk for entry Fi and moves its content to memory** (Unit 5_Part 1_File-system-interface, p.7; judge: supported)
- Unit 5 | What alternative names are given to partitions on a disk? -> **minidisks, slices** (Unit 5_Part 1_File-system-interface, p.16; judge: supported)
- Unit 5 | According to the Unix file system (UFS) consistency semantics, when are writes to an open file visible to other users? -> **Immediately to other users of the same open file** (Unit 5_Part 1_File-system-interface, p.36; judge: supported)
- Unit 5 | Using a bitmap free-space management scheme, how many bits are needed to represent a 1‐gigabyte disk with a block size of 2^12 bytes? -> **262,144 bits** (Unit 5_Part 1_File-system-interface, p.56; judge: supported)
- Unit 5 | What effect does the setuid bit have when a file with this bit set is executed? -> **The user‐id is set to the owner of the file being executed** (Unit 5_Part 2_System Protection, p.7; judge: supported)
