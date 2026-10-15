# Answers for manual spot check - split `test`

Check each: is every sentence supported by the cited slide? Is anything important missing? Note disagreements with the judge in NOTES.md.

## 21. What are the four components of a computer system?

*concise; answered; judge unsupported: []*

The computer system has four components: hardware, which provides basic computing resources such as the CPU, memory, and I/O devices [1]. The operating system, which controls and coordinates the use of hardware among applications and users [1]. Application programs, which define how system resources are used to solve users’ computing problems, such as word processors, compilers, web browsers, database systems, and video games [1]. Users, which include people, machines, and other computers [1].

- [1] Unit 1_Part 1_Introduction & OS Structure, p.11 - Computer system can be divided into four components: Computer system can be divided into four components • Hardware – provides basic computing resources, ex. CPU, memory, I/O devices • Operating system - Controls and coordinates use of hardware among various applications and users • Applicati

## 22. Besides user services, which three services does the OS provide to keep the system itself running efficiently?

*concise; answered; judge unsupported: []*

The OS provides resource allocation to distribute system resources among users and jobs [1]. It performs accounting to record each user’s consumption of resources [1]. It ensures protection so that processes cannot interfere with each other or the OS and enforces security through authentication [1].

- [1] Unit 1_Part 1_Introduction & OS Structure, p.16 - Operating System Services: Operating System Services Following are the three services provided by operating systems for ensuring the efficient operation of the system itself. 1. Resource allocation When multiple users are logged on the system or multiple jobs are run

## 23. What is a real-time operating system, what types exist and what are its advantages?

*concise; answered; judge unsupported: []*

A Real‐Time Operating System (RTOS) is designed to handle time‐sensitive tasks where processing must occur within a strict deadline [1]. The types of real‐time operating systems are Hard Real‐Time, Soft Real‐Time, and Firm Real‐Time [1]. The notes do not provide any listed advantages of a real‐time operating system.

- [1] Unit 1_Part 1_Introduction & OS Structure, p.37 - An Operating system, which includes: In Real-Time Systems, each job carries a certain A Real-Time Operating System (RTOS) is designed to handle time-sensitive tasks where processing must occur within a strict deadline. deadline within which the job is supposed to be completed,

## 25. Using exponential averaging with alpha 0.5, what is the predicted burst time for the fifth process?

*concise; answered; judge unsupported: []*

The predicted burst time for the fifth process is 6.875 units [2].

- [2] Unit 1_Part 2_ Process management, p.63 - Example: Example Predicted Burst Time for 4th Process- Predicted burst time for 4th process = α x Actual burst time of 3rd process + (1-α) x Predicted burst time for 3rd process = 0.5 x 6 + 0.5 x 7.5 = 3 + 3.75 = 6.75 units Predicted Burst Time for 

## 26. What is the convoy effect in FCFS CPU scheduling?

*concise; answered; judge unsupported: []*

The convoy effect occurs when processes with long CPU bursts arrive before those with short bursts, causing the short processes to wait a long time while the long processes hold the CPU [1].

- [1] Unit 1_Part 2_ Process management, p.48 - First Come First Serve: First Come First Serve Advantages of FCFS : • Simple • Easy, useful and understandable Convoy Effect In convoy effect, •Consider processes with higher burst time arrived before the processes with smaller burst time. •Then, smaller processes

## 27. What are the five basic states a process goes through from creation to termination?

*concise; answered; judge unsupported: []*

New: a program that the OS will load into main memory [2]. Ready: the process waits in main memory for the CPU to be assigned [2]. Running: a ready process is chosen by the OS and executed [1]. Block or wait: a running process may move to this state while waiting for a resource or input [1]. Termination: the process finishes execution and its context is deleted by the OS [1]. The notes do not list the exact five state names, but these five are described.

- [2] Unit 1_Part 2_ Process management, pp.8-9 - Process States: Process States Process States The process, from its creation to completion, passes through various states. The minimum number of states is five. The names of the states are not standardized although the process may be in one of the followin
- [1] Unit 1_Part 2_ Process management, p.10 - Process States: Process States 3. Running : One of the processes from the ready state will be chosen by the OS depending upon the scheduling algorithm 4. Block or wait : From the Running state, a process can make the transition to the block or wait state d

## 28. What happens to the whole process when a user-level thread performs a blocking operation, compared with a kernel-level thread?

*concise; answered; judge unsupported: []*

When a user‐level thread performs a blocking operation, the entire process is blocked [1]. If a kernel‐level thread performs a blocking operation, other threads in the same process can continue executing [1].

- [1] Unit 1_Part 2_ Process management, p.108 - Types of Thread: Types of Thread User Level threads Kernel Level Threads These threads are implemented by users. These threads are implemented by Operating systems These threads are not recognized by operating systems, These threads are recognized by operat

## 29. What is the minimum number of units of a resource that guarantees no deadlock for n processes?

*concise; answered; judge unsupported: []*

The minimum number of units of a resource that guarantees no deadlock for n processes is one more than the sum of each process’s maximum demand minus n, i.e., (∑ xi – n) + 1 [2].

- [2] Unit 2_Process Synchronization_Deadlock, p.30 - Maximum Number Of Units That Ensures Deadlock-: Maximum Number Of Units That Ensures Deadlock- Maximum number of units of resource R that ensures deadlock = (x1-1) + (x2-1) + (x3-1) + …. + (xn-1) = ( x1 + x2 + x3 + …. + xn ) – n = ∑xi – n = Sum of max needs of all n processes – n Minimum

## 31. Which data structures (Available, Max, Allocation, Need) does the Banker's algorithm maintain and what do they mean?

*concise; answered; judge unsupported: []*

The Banker's algorithm maintains an Available vector that shows how many instances of each resource type are currently free [1]. It keeps a Max matrix that records the maximum number of each resource that each process may request [1]. It also uses an Allocation matrix that indicates how many resources of each type are presently allocated to each process [1]. Finally, it computes a Need matrix, defined as Max minus Allocation, representing the remaining resources each process may still require [1].

- [1] Unit 2_Process Synchronization_Deadlock, p.48 - Banker's algorithm: Several data structures must be maintained to implement the banker's algorithm. These data structures encode the state of the resource-allocation system. Let n be the number of processes in the system and m be the number of resource types. 

## 32. What is the difference between a safe state and an unsafe state?

*concise; answered; judge unsupported: []*

A safe state is one in which there exists a safe execution sequence that allows each process to run to termination or to a blocked state while all resource requests can be granted immediately if the resources are available [1]. An unsafe state is one in which no safe execution sequence exists; such a state may not be deadlocked yet there is at least one possible sequence of requests that could lead to deadlock [1].

- [1] Unit 2_Process Synchronization_Deadlock, p.38 - Safe and Unsafe States: Safe and Unsafe States ➢A system is said to be in a Safe State, if there is a safe execution sequence. An execution sequence is an ordering for process execution such that each process runs until it terminates or blocked and all request for

## 33. In the first and second readers-writers problems, who can starve?

*concise; answered; judge unsupported: []*

In the first readers‐writers problem, writers can be starved because readers are given priority and may keep arriving continuously [1]. In the second readers‐writers problem, readers can be starved because writers are given priority and may keep arriving continuously [1].

- [1] Unit 2_Process Synchronization_Deadlock, p.17 - The Readers Writers Problem: The Readers Writers Problem There are several variations to the readers-writers problem, most centered around relative priorities of readers versus writers. • The first readers-writers problem gives priority to readers. In this problem, if 

## 34. What are the advantages and disadvantages of dynamic partitioning?

*concise; answered; judge unsupported: []*

Dynamic partitioning is simple to implement [1]. It has no internal fragmentation [1]. It imposes no limitation on the size of a process [1]. The degree of multiprogramming is dynamic [1]. It is easy to manage and design [1][2]. A disadvantage is that it suffers from external fragmentation [1]. The number of partitions must be specified at the time of system segmentation [1].

- [1] Unit 3_Memory management, pp.15-16 - Multiple Partitioning: Multiple Partitioning Dynamic Partitioning MEMORY MANAGEMENT Multiple Partitioning Dynamic Partitioning Advantages: MEMORY MANAGEMENT • Simple to implement. • No Internal Fragmentation • No Limitation on the size of the process • Degree of 
- [2] Unit 3_Memory management, p.14 - Multiple Partitioning: Multiple Partitioning Dynamic Partitioning ▪The dynamic partitioning was designed to overcome the problems of a MEMORY MANAGEMENT fixed partitioning scheme. ▪In a dynamic partitioning scheme, each process occupies only as much memory as the

## 35. For a logical address space of eight pages of 1024 words mapped onto 32 frames, how many bits are in the logical and physical addresses?

*concise; answered; judge unsupported: []*

The logical address requires 13 bits: 3 bits for the page number and 10 bits for the offset within a page [2]. The physical address requires 15 bits: 5 bits for the frame number and 10 bits for the offset within a frame [1].

- [2] Unit 3_Memory management, p.41 - Paging Practice Problems: Paging Practice Problems Problem: Consider a logical address space of eight pages of 1024 words each, mapped onto a physical memory of 32 page frames. (a) How many bits are in logical address? How many bits represent for the page number and
- [1] Unit 3_Memory management, p.42 - Paging Practice Problems: Paging Practice Problems Problem: Consider a logical address space of eight pages of 1024 words each, mapped onto a physical memory of 32 page frames. (a) How many bits are in logical address? How many bits represent for the page number and

## 37. How many page faults does LRU page replacement give for the reference string with three frames?

*concise; answered; judge unsupported: []*

The LRU page‐replacement algorithm produces 13 page faults for the given reference string with three frames [1].

- [1] Unit 3_Memory management, p.49 - Example: Example Consider the reference string 6, 1, 1, 2, 0, 3, 4, 6, 0, 2, 1, 2, 1, 2, 0, 3, 2, 1, 2, 0 for a memory with three frames and calculate number of page faults by using LRU (Least Recently Used) Page replacement algorithms. PAGING Point

## 38. Why is the SCAN disk scheduling algorithm called the elevator algorithm?

*concise; answered; judge unsupported: []*

The algorithm moves the disk head in one direction, serving all requests until it reaches the end of the disk, then reverses and scans back serving requests again, just like an elevator moving to the top floor and then back down [1].

- [1] Unit 4_Storage management_ Disk Schduling, p.15 - SCAN Disk Scheduling Algorithm: SCAN Disk Scheduling Algorithm In this algorithm, the head starts to scan all the requests in a direction and reaches the end of the disk. After that, it reverses its direction and starts to scan again the requests in its path and serves th

## 39. What is the total seek time for C-LOOK on the request sequence 82, 170, 43, 140, 24, 16, 190 with the head at 50?

*concise; answered; judge unsupported: []*

The total seek time for C‐LOOK on that request sequence with the head starting at 50 is 341. [1]

- [1] Unit 4_Storage management_ Disk Schduling, p.25 - C-LOOK Disk Scheduling Algorithm: C-LOOK Disk Scheduling Algorithm Example: Suppose a disk having 200 tracks (0-199). The request sequence(82,170,43,140,24,16,190) of disk are shown as in the given figure and the head start is at request 50. Seek time= (190-50) + (190-16) +

## 40. What is the difference between mandatory and advisory file locking?

*concise; answered; judge unsupported: []*

Mandatory locking causes the operating system to deny access to a file based on the locks that are held and the locks that are requested [1]. Advisory locking only lets processes query the lock status and then choose their own actions; the system does not enforce denial of access [1].

- [1] Unit 5_Part 1_File-system-interface, p.9 - OPEN FILE LOCKING: OPEN FILE LOCKING • Provided by some operating systems and file systems • Mediates access to a file • Mandatory or advisory: • Mandatory – access is denied depending on locks held and requested • Advisory – processes can find status of lock

## 41. What are the advantages and drawbacks of contiguous allocation of disk blocks?

*concise; answered; judge unsupported: []*

Contiguous allocation is simple because only the starting block number and the length of the file need to be stored [2]. It allows random access to any block within the file [2]. The scheme can waste space due to the dynamic storage‐allocation problem [2]. It also prevents files from growing after they are created [2].

- [2] Unit 5_Part 1_File-system-interface, p.46 - CONTIGUOUS ALLOCATION: CONTIGUOUS ALLOCATION • Each file occupies a set of contiguous blocks on the disk • Simple – only starting location (block #) and length (number of blocks) are required • Random access • Wasteful of space (dynamic storage-allocation problem

## 43. What is the principle of least privilege?

*concise; answered; judge unsupported: []*

The principle of least privilege means giving programs, users, and systems only the privileges needed to perform their tasks [1]. It limits damage if an entity has a bug or is abused [1].

- [1] Unit 5_Part 2_System Protection, p.5 - Principles of Protection: Principles of Protection • Guiding principle – principle of least privilege • Programs, users and systems should be given just enough privileges to perform their tasks • Limits damage if entity has a bug, gets abused • Can be static (during

## 44. How do access lists for objects differ from capability lists for domains when implementing the access matrix?

*concise; answered; judge unsupported: []*

Access lists for objects are stored as columns, each containing ordered pairs of a domain and its rights‐set for that object [2][3]. 
Capability lists for domains are stored as rows, each listing the objects and the operations the domain may perform on them [3][1].

- [2] Unit 5_Part 2_System Protection, pp.17-18 - Implementation of Access Matrix: Modified Access Matrix of Figure B Implementation of Access Matrix • Generally, a sparse matrix • Option 1 – Global table • Store ordered triples < domain, object, rights-set > in table • A requested operation M on object Oj within domain D
- [3] Unit 5_Part 2_System Protection, p.19 - Implementation of Access Matrix: • Each column = Access-control list for one object Defines who can perform what operation Domain 1 = Read, Write Domain 2 = Read Domain 3 = Read • Each Row = Capability List (like a key) For each domain, what operations allowed on what obje
- [1] Unit 5_Part 2_System Protection, p.20 - Implementation of Access Matrix (Cont.): Implementation of Access Matrix (Cont.) • Option 3 – Capability list for domains • Instead of object-based, list is domain based • Capability list for domain is list of objects together with operations allows on them • Object represented by

