# Answers for manual spot check - split `dev`

Check each: is every sentence supported by the cited slide? Is anything important missing? Note disagreements with the judge in NOTES.md.

## 1. What are the two parts of an operating system and what does each one do?

*concise; answered; judge unsupported: []*

An operating system consists of two parts: the kernel, which is the always‐running component that interacts directly with the hardware (e.g., device drivers, system files) [1]; and the shell, which is the command‐interpreter—a set of programs that lets users interact with applications and executes the commands given to the OS [1].

- [1] Unit 1_Part 1_Introduction & OS Structure, p.12 - Components of a Computer System: Components of a Computer System Components of OS: OS has two parts. (1) Kernel is an active part of an OS i.e., it is the part of OS running at all times. It is a program which can interact with the hardware. Ex: Device driver, .dll files, 

## 2. Which five services does an operating system provide for the convenience of its users?

*concise; answered; judge unsupported: [1]*

The operating system provides these five user‐convenience services: program execution, I/O operations, file‐system manipulation, resource allocation, and protection[1].

- [1] Unit 1_Part 1_Introduction & OS Structure, pp.13-14 - Operating System Services: A View of Operating System Services Operating System Services Following are the five services provided by operating systems to the convenience of the users. 1. Program Execution The purpose of computer systems is to allow the user to execut

## 3. What are the user mode and kernel mode, and what is a system call?

*concise; answered; judge unsupported: not checked*

User mode is the execution state in which a program runs with limited privileges, while kernel mode is the privileged state where the operating system’s core functions can directly access hardware and memory resources[1]. A system call is the mechanism by which a user‐mode program requests a service from the kernel, causing a transition from user mode to kernel mode and back after the request is handled[1][2].

- [1] Unit 1_Part 1_Introduction & OS Structure, p.43 - What is a System Call: What is a System Call A computer operates in two modes: User mode and Kernel mode. The execution of a program is in the user mode. When the program requires RAM or a hardware resource, it sends a request to the kernel and the mode changes f
- [2] Unit 1_Part 1_Introduction & OS Structure, p.44 - What is a System Call: shell: acts as an intermediary b/w user and system call. Interpret user command and makes system calls. System Calls ➢A system call is a method for a computer program to request a service from the kernel of the operating system on which it 

## 4. What does the dispatcher do and which steps does it involve?

*concise; answered; judge unsupported: []*

The dispatcher is the OS module that actually gives the CPU to a selected process, performing the final allocation after the short‐term scheduler chooses it. It carries out three actions: it performs a context‐switch, switches the CPU to user mode, and then jumps to the correct location in the user program to resume execution[1].

- [1] Unit 1_Part 2_ Process management, p.40 - Dispatcher: Dispatcher A Dispatcher is that module of the operating system which gives control of the CPU to the process. Short term scheduler only decides which process to allocate to CPU. Whereas the dispatcher actually allocates the CPU to that proc

## 5. How does the size of the time quantum affect context switches, response time and starvation in round robin scheduling?

*concise; answered; judge unsupported: []*

A smaller time quantum increases the number of context switches, reduces response time, and lowers the chance of starvation[1]. Conversely, a larger time quantum decreases the number of context switches, raises response time, and raises the chance of starvation[2]. The notes do not give exact quantitative values for these effects.

- [1] Unit 1_Part 2_ Process management, p.75 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm Note-01: With decreasing value of time quantum, ➢Number of context switch increases ➢Response time decreases ➢Chances of starvation decreases Thus, smaller value of time quantum is better in terms of respons
- [2] Unit 1_Part 2_ Process management, p.76 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm Note-02: With increasing value of time quantum, ➢Number of context switch decreases ➢Response time increases ➢Chances of starvation increases Thus, higher value of time quantum is better in terms of number o

## 6. Which system calls does a parent use to create a child process and to wait for it to finish?

*concise; answered; judge unsupported: []*

A parent creates a child process with the fork system call and then blocks until the child finishes using the wait system call [1][5].

- [1] Unit 1_Part 2_ Process management, p.34 - Process Creation: Process Creation The following system calls are used for basic process management. fork : A parent process uses fork to create a new child process. The child process is a copy of the parent. After fork, both parent and child executes the sa
- [5] Unit 1_Part 2_ Process management, p.36 - Process Creation: #include<stdio.h> void main(int argc, char *argv[]) { int pid; /* Fork another process */ pid = fork(); if(pid < 0) { //Error occurred fprintf(stderr, "Fork Failed"); exit(-1); } else if (pid == 0) { //Child process execlp("/bin/ls","ls",NU

## 7. Which multithreading model gives every user thread its own kernel thread?

*concise; answered; judge unsupported: not checked*

The one‐to‐one model creates a separate kernel thread for each user thread, giving every user thread its own kernel thread[3].

- [3] Unit 1_Part 2_ Process management, pp.114-115 - One to One Model: Many to One Model One to One Model ❖The one to one model creates a separate kernel thread to handle each and every user thread. ❖Most implementations of this model place a limit on how many threads can be created. ❖Linux and Windows from 95

## 8. What three requirements must a solution to the critical section problem satisfy?

*concise; answered; judge unsupported: []*

A correct solution must guarantee **mutual exclusion** so that only one process can be in its critical section at a time, ensure **progress** so that if no process is in the critical section, a waiting process will eventually be allowed to enter, and provide **bounded waiting** so that a requesting process will get its turn after a limited number of other entries [3].

- [3] Unit 2_Process Synchronization_Deadlock, p.6 - Rules for Critical Section: Rules for Critical Section 1. Mutual Exclusion: Only one process at a time can be executing in their critical section. 2. Progress: If no process is currently executing in their critical section, and one or more processes want to execute th

## 9. How do binary semaphores differ from counting semaphores?

*concise; answered; judge unsupported: []*

Binary semaphores can only hold the values 0 or 1 and are typically used to enforce mutual exclusion like a mutex [2]. Counting semaphores can hold any non‐negative integer, representing the number of available instances of a limited resource and allowing multiple processes to enter the critical section while the count is positive [1].

- [2] Unit 2_Process Synchronization_Deadlock, p.11 - Types of Semaphore: Types of Semaphore semaphores can take on one of two forms: Binary semaphores can take on one of two values, 0 or 1. They can be used to solve the critical section, and can be used as mutexes on systems that do not provide a separate mutex 
- [1] Unit 2_Process Synchronization_Deadlock, p.12 - Types of Semaphore: Types of Semaphore Counting semaphores can take on any integer value, and are usually used to count the number remaining of some limited resource. ▪The counter is initialized to the number of such resources available in the system, and when

## 10. What does a cycle in a resource allocation graph tell us when every resource has a single instance?

*concise; answered; judge unsupported: []*

If a cycle appears in a resource‐allocation graph and each resource has only one instance, the system is deadlocked [2].

- [2] Unit 2_Process Synchronization_Deadlock, p.44 - Deadlock Detection using RAG: Deadlock Detection using RAG ➢If a cycle is being formed in a Resource allocation graph where all the resources have the single instance then the system is deadlocked. ➢In Case of Resource allocation graph with multi-instanced resource type

## 11. Which of first fit, best fit and worst fit used memory most efficiently for the 212 KB, 417 KB, 112 KB and 426 KB requests?

*concise; answered; judge unsupported: []*

The best‐fit algorithm used memory most efficiently for the 212 KB, 417 KB, 112 KB and 426 KB requests, as it was the only algorithm that could satisfy all four memory requests[1][3].

- [1] Unit 3_Memory management, p.22 - DYNAMIC STORAGE-ALLOCATION PROBLEM: DYNAMIC STORAGE-ALLOCATION PROBLEM c) Worst-fit The worst-fit algorithm effectively selects the largest partition for each request. Worst-fit would allocate in the following manner: 212 KB => 600 KB, leaving a 388 KB partition 417 KB => 500
- [3] Unit 3_Memory management, p.21 - DYNAMIC STORAGE-ALLOCATION PROBLEM: DYNAMIC STORAGE-ALLOCATION PROBLEM b) Best-fit The best-fit algorithm selects the partition whose size is closest in size (and large enough) to the requested size. Best-fit would allocate in the following manner: 212 KB => 300 KB, leaving a

## 12. What is a TLB and why is it used with page tables?

*concise; answered; judge unsupported: []*

A TLB (Translation Look‐aside Buffer) is a small, high‐speed associative memory that caches recent page‐table translations. It is used with page tables because looking up a full page table in memory can be slow, especially when the table has many entries, so the TLB provides a fast hardware cache to speed up address translation [1].

- [1] Unit 3_Memory management, p.43 - MAPPING FROM PAGE TABLE TO MAIN MEMORY: MAPPING FROM PAGE TABLE TO MAIN MEMORY Dedicated registers can be used to implement the page table in hardware. However, using a register for the page table is only useful if the page table is tiny. We can PAGING employ TLB (translation loo

## 13. How many page faults does FIFO page replacement produce for the reference string with three frames?

*concise; answered; judge unsupported: []*

FIFO page replacement produces 12 page faults for the given reference string with three frames[1].

- [1] Unit 3_Memory management, p.48 - Example: Example Consider the reference string 6, 1, 1, 2, 0, 3, 4, 6, 0, 2, 1, 2, 1, 2, 0, 3, 2, 1, 2, 0 for a memory with three frames and calculate number of page faults by using FIFO (First In First Out) Page replacement algorithms. PAGING Point

## 14. What is the total seek time for FCFS disk scheduling on a 200-track disk with the head starting at 50?

*concise; abstained: model; judge unsupported: not checked*

Not in your notes.

- [1] Unit 4_Storage management_ Disk Schduling, p.22 - LOOK Disk Scheduling Algorithm: LOOK Disk Scheduling Algorithm Example: Suppose a disk having 200 tracks (0-199). The request sequence(82,170,43,140,24,16,190) of disk are shown as in the given figure and the head start is at request 50. Seek time= (190-50) + (190-16) =31
- [2] Unit 4_Storage management_ Disk Schduling, p.25 - C-LOOK Disk Scheduling Algorithm: C-LOOK Disk Scheduling Algorithm Example: Suppose a disk having 200 tracks (0-199). The request sequence(82,170,43,140,24,16,190) of disk are shown as in the given figure and the head start is at request 50. Seek time= (190-50) + (190-16) +
- [3] Unit 4_Storage management_ Disk Schduling, p.16 - SCAN Disk Scheduling Algorithm: SCAN Disk Scheduling Algorithm Example: Suppose a disk having 200 tracks (0-199). The request sequence(82,170,43,140,24,16,190) of disk are shown as in the given figure and the head start is at request 50. Seek time= (199-50) + (199-16) =33

## 15. What are the advantages and disadvantages of the shortest seek time first disk scheduling algorithm?

*concise; answered; judge unsupported: not checked*

The Shortest Seek Time First algorithm gives a lower disk response time and is more efficient than FCFS[1]. Its drawbacks are that the algorithm runs more slowly and it can cause starvation of some requests[1].

- [1] Unit 4_Storage management_ Disk Schduling, p.14 - Shortest Seek Time First: Shortest Seek Time First Advantages: • In this algorithm, disk response time is less. • More efficient than FCFS. Disadvantages: • Less speed of algorithm execution. • Starvation can be seen.

## 16. What are the three methods of allocating disk blocks to files?

*concise; answered; judge unsupported: not checked*

The three methods of allocating disk blocks to files are contiguous allocation, linked allocation, and indexed allocation [1].

- [1] Unit 5_Part 1_File-system-interface, pp.44-45 - ALLOCATION METHODS: A TYPICAL FILE CONTROL BLOCK ALLOCATION METHODS • An allocation method refers to how disk blocks are allocated for files: • Contiguous allocation • Linked allocation • Indexed allocation

## 17. How can a dangling pointer be avoided when a file shared in an acyclic-graph directory is deleted?

*concise; answered; judge unsupported: not checked*

Use backpointers (or a daisy‐chain of backpointers) so that when a shared file is removed the system can locate and delete every directory entry that still points to it, preventing any dangling pointers [1].

- [1] Unit 5_Part 1_File-system-interface, p.26 - ACYCLIC-GRAPH DIRECTORIES: ACYCLIC-GRAPH DIRECTORIES (CONT.) • Two different names (aliasing) • If dict deletes list dangling pointer Solutions: • Backpointers, so we can delete all pointers Variable size records a problem • Backpointers using a daisy chain organizat

