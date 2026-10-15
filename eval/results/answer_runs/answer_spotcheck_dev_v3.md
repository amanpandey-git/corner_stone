# Answers for manual spot check - split `dev`

Check each: is every sentence supported by the cited slide? Is anything important missing? Note disagreements with the judge in NOTES.md.

## 1. What are the two parts of an operating system and what does each one do?

*concise; answered; judge unsupported: []*

The operating system consists of two parts: the kernel and the shell. The kernel is the active part of the OS that runs continuously and can interact directly with the hardware, such as device drivers,.dll files and system files [1]. The shell is the command interpreter, a set of programs used to interact with application programs and to execute the commands given to the OS [1].

- [1] Unit 1_Part 1_Introduction & OS Structure, p.12 - Components of a Computer System: Components of a Computer System Components of OS: OS has two parts. (1) Kernel is an active part of an OS i.e., it is the part of OS running at all times. It is a program which can interact with the hardware. Ex: Device driver, .dll files, 

## 2. Which five services does an operating system provide for the convenience of its users?

*concise; answered; judge unsupported: []*

Program execution service lets users run programs by handling memory allocation and CPU scheduling [1]. 
I/O operations service provides input and output handling for programs [1]. 
File system manipulation service lets programs read from and write to files [1]. 
Resource allocation service distributes resources among multiple users or jobs [2]. 
Protection service controls access to system resources and secures the system [2].

- [1] Unit 1_Part 1_Introduction & OS Structure, pp.13-14 - Operating System Services: A View of Operating System Services Operating System Services Following are the five services provided by operating systems to the convenience of the users. 1. Program Execution The purpose of computer systems is to allow the user to execut
- [2] Unit 1_Part 1_Introduction & OS Structure, p.16 - Operating System Services: Operating System Services Following are the three services provided by operating systems for ensuring the efficient operation of the system itself. 1. Resource allocation When multiple users are logged on the system or multiple jobs are run

## 3. What are the user mode and kernel mode, and what is a system call?

*concise; answered; judge unsupported: []*

User mode is the mode in which a program’s execution runs, while kernel mode is the privileged mode where the operating system kernel operates and can access hardware resources [1]. When a program needs RAM or a hardware resource, it sends a request that switches execution from user mode to kernel mode, performs the request, and then returns to user mode; this request is called a system call [1][2]. A system call is a method for a program to request a service from the operating system’s kernel [2].

- [1] Unit 1_Part 1_Introduction & OS Structure, p.43 - What is a System Call: What is a System Call A computer operates in two modes: User mode and Kernel mode. The execution of a program is in the user mode. When the program requires RAM or a hardware resource, it sends a request to the kernel and the mode changes f
- [2] Unit 1_Part 1_Introduction & OS Structure, p.44 - What is a System Call: shell: acts as an intermediary b/w user and system call. Interpret user command and makes system calls. System Calls ➢A system call is a method for a computer program to request a service from the kernel of the operating system on which it 

## 4. What does the dispatcher do and which steps does it involve?

*concise; answered; judge unsupported: []*

The dispatcher gives control of the CPU to a process [1]. It performs three steps: first it does a context switch, then it switches to user mode, and finally it jumps to the proper location in the user program to restart the process [1].

- [1] Unit 1_Part 2_ Process management, p.40 - Dispatcher: Dispatcher A Dispatcher is that module of the operating system which gives control of the CPU to the process. Short term scheduler only decides which process to allocate to CPU. Whereas the dispatcher actually allocates the CPU to that proc

## 5. How does the size of the time quantum affect context switches, response time and starvation in round robin scheduling?

*concise; answered; judge unsupported: []*

A smaller time quantum increases the number of context switches, reduces response time, and lowers the chances of starvation [1]. A larger time quantum decreases the number of context switches, increases response time, and raises the chances of starvation [2]. The notes do not discuss any additional effects beyond these three aspects.

- [1] Unit 1_Part 2_ Process management, p.75 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm Note-01: With decreasing value of time quantum, ➢Number of context switch increases ➢Response time decreases ➢Chances of starvation decreases Thus, smaller value of time quantum is better in terms of respons
- [2] Unit 1_Part 2_ Process management, p.76 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm Note-02: With increasing value of time quantum, ➢Number of context switch decreases ➢Response time increases ➢Chances of starvation increases Thus, higher value of time quantum is better in terms of number o

## 6. Which system calls does a parent use to create a child process and to wait for it to finish?

*concise; answered; judge unsupported: []*

A parent creates a child process with the fork system call [1]. After the child finishes, the parent waits for it using the wait system call [1][3].

- [1] Unit 1_Part 2_ Process management, p.34 - Process Creation: Process Creation The following system calls are used for basic process management. fork : A parent process uses fork to create a new child process. The child process is a copy of the parent. After fork, both parent and child executes the sa
- [3] Unit 1_Part 2_ Process management, p.37 - Wait: Wait The wait system call blocks the caller until one of its child process terminates. If the caller doesn’t have any child processes, wait returns immediately without blocking the caller. Using wait the parent can obtain the exit status of

## 7. Which multithreading model gives every user thread its own kernel thread?

*concise; answered; judge unsupported: []*

The One to One Model creates a separate kernel thread for each user thread [3].

- [3] Unit 1_Part 2_ Process management, pp.114-115 - One to One Model: Many to One Model One to One Model ❖The one to one model creates a separate kernel thread to handle each and every user thread. ❖Most implementations of this model place a limit on how many threads can be created. ❖Linux and Windows from 95

## 8. What three requirements must a solution to the critical section problem satisfy?

*concise; answered; judge unsupported: []*

A solution must guarantee Mutual Exclusion, allowing only one process in its critical section at a time [3]. 
It must ensure Progress, so that if no process is in the critical section and some want to enter, the decision to allow entry is made without indefinite postponement [3]. 
It must provide Bounded Waiting, meaning a requesting process will eventually be granted entry and only a limited number of other processes can enter before it [3].

- [3] Unit 2_Process Synchronization_Deadlock, p.6 - Rules for Critical Section: Rules for Critical Section 1. Mutual Exclusion: Only one process at a time can be executing in their critical section. 2. Progress: If no process is currently executing in their critical section, and one or more processes want to execute th

## 9. How do binary semaphores differ from counting semaphores?

*concise; answered; judge unsupported: []*

Binary semaphores can only have the values 0 or 1 [2]. Counting semaphores can hold any integer value, typically representing the number of available resources [1]. Binary semaphores are often used as simple locks or mutexes, while counting semaphores are used to track multiple instances of a resource [1][2].

- [2] Unit 2_Process Synchronization_Deadlock, p.11 - Types of Semaphore: Types of Semaphore semaphores can take on one of two forms: Binary semaphores can take on one of two values, 0 or 1. They can be used to solve the critical section, and can be used as mutexes on systems that do not provide a separate mutex 
- [1] Unit 2_Process Synchronization_Deadlock, p.12 - Types of Semaphore: Types of Semaphore Counting semaphores can take on any integer value, and are usually used to count the number remaining of some limited resource. ▪The counter is initialized to the number of such resources available in the system, and when

## 10. What does a cycle in a resource allocation graph tell us when every resource has a single instance?

*concise; answered; judge unsupported: []*

If a cycle appears in a resource‐allocation graph and each resource has only one instance, the system is deadlocked [2].

- [2] Unit 2_Process Synchronization_Deadlock, p.44 - Deadlock Detection using RAG: Deadlock Detection using RAG ➢If a cycle is being formed in a Resource allocation graph where all the resources have the single instance then the system is deadlocked. ➢In Case of Resource allocation graph with multi-instanced resource type

## 11. Which of first fit, best fit and worst fit used memory most efficiently for the 212 KB, 417 KB, 112 KB and 426 KB requests?

*concise; answered; judge unsupported: []*

The best‐fit algorithm used memory most efficiently for the 212 KB, 417 KB, 112 KB and 426 KB requests [1][3]. It was the only algorithm that could satisfy all four memory requests, while first‐fit and worst‐fit each failed to allocate the 426 KB request [2][1].

- [1] Unit 3_Memory management, p.22 - DYNAMIC STORAGE-ALLOCATION PROBLEM: DYNAMIC STORAGE-ALLOCATION PROBLEM c) Worst-fit The worst-fit algorithm effectively selects the largest partition for each request. Worst-fit would allocate in the following manner: 212 KB => 600 KB, leaving a 388 KB partition 417 KB => 500
- [3] Unit 3_Memory management, p.21 - DYNAMIC STORAGE-ALLOCATION PROBLEM: DYNAMIC STORAGE-ALLOCATION PROBLEM b) Best-fit The best-fit algorithm selects the partition whose size is closest in size (and large enough) to the requested size. Best-fit would allocate in the following manner: 212 KB => 300 KB, leaving a
- [2] Unit 3_Memory management, p.20 - DYNAMIC STORAGE-ALLOCATION PROBLEM: DYNAMIC STORAGE-ALLOCATION PROBLEM 1. Given memory partitions of 100 KB, 500 KB, 200 KB, 300 KB, and 600 KB, how would each of the first fit, best fit and worst fit algorithms place processes of 212 KB, 417 KB, 112 KB and 426 KB? Which algo

## 12. What is a TLB and why is it used with page tables?

*concise; answered; judge unsupported: []*

A TLB (translation look‐aside buffer) is a tiny, fast, associative memory cache used to look up page‐table entries quickly [1]. It is employed when the page table has many entries because a register‐based page table is only practical for a very small table, so the TLB speeds up address translation for larger page tables [1].

- [1] Unit 3_Memory management, p.43 - MAPPING FROM PAGE TABLE TO MAIN MEMORY: MAPPING FROM PAGE TABLE TO MAIN MEMORY Dedicated registers can be used to implement the page table in hardware. However, using a register for the page table is only useful if the page table is tiny. We can PAGING employ TLB (translation loo

## 13. How many page faults does FIFO page replacement produce for the reference string with three frames?

*concise; answered; judge unsupported: []*

FIFO page replacement produces 12 page faults for the given reference string with three frames [1].

- [1] Unit 3_Memory management, p.48 - Example: Example Consider the reference string 6, 1, 1, 2, 0, 3, 4, 6, 0, 2, 1, 2, 1, 2, 0, 3, 2, 1, 2, 0 for a memory with three frames and calculate number of page faults by using FIFO (First In First Out) Page replacement algorithms. PAGING Point

## 14. What is the total seek time for FCFS disk scheduling on a 200-track disk with the head starting at 50?

*concise; abstained: model; judge unsupported: not checked*

Not in your notes.

- [1] Unit 4_Storage management_ Disk Schduling, p.22 - LOOK Disk Scheduling Algorithm: LOOK Disk Scheduling Algorithm Example: Suppose a disk having 200 tracks (0-199). The request sequence(82,170,43,140,24,16,190) of disk are shown as in the given figure and the head start is at request 50. Seek time= (190-50) + (190-16) =31
- [2] Unit 4_Storage management_ Disk Schduling, p.25 - C-LOOK Disk Scheduling Algorithm: C-LOOK Disk Scheduling Algorithm Example: Suppose a disk having 200 tracks (0-199). The request sequence(82,170,43,140,24,16,190) of disk are shown as in the given figure and the head start is at request 50. Seek time= (190-50) + (190-16) +
- [3] Unit 4_Storage management_ Disk Schduling, p.16 - SCAN Disk Scheduling Algorithm: SCAN Disk Scheduling Algorithm Example: Suppose a disk having 200 tracks (0-199). The request sequence(82,170,43,140,24,16,190) of disk are shown as in the given figure and the head start is at request 50. Seek time= (199-50) + (199-16) =33

## 15. What are the advantages and disadvantages of the shortest seek time first disk scheduling algorithm?

*concise; answered; judge unsupported: []*

The algorithm has less disk response time [1]. It is more efficient than FCFS [1]. It has slower algorithm execution speed [1]. Starvation can occur with it [1].

- [1] Unit 4_Storage management_ Disk Schduling, p.14 - Shortest Seek Time First: Shortest Seek Time First Advantages: • In this algorithm, disk response time is less. • More efficient than FCFS. Disadvantages: • Less speed of algorithm execution. • Starvation can be seen.

## 16. What are the three methods of allocating disk blocks to files?

*concise; answered; judge unsupported: []*

Contiguous allocation is one method of allocating disk blocks to files [1]. Linked allocation is another method [1]. Indexed allocation is the third method [1].

- [1] Unit 5_Part 1_File-system-interface, pp.44-45 - ALLOCATION METHODS: A TYPICAL FILE CONTROL BLOCK ALLOCATION METHODS • An allocation method refers to how disk blocks are allocated for files: • Contiguous allocation • Linked allocation • Indexed allocation

## 17. How can a dangling pointer be avoided when a file shared in an acyclic-graph directory is deleted?

*concise; answered; judge unsupported: []*

Use backpointers so that when a file is deleted all pointers to it can be found and removed [1]. 
Alternatively, organize pointers in a daisy‐chain or keep an entry‐hold count to track how many names refer to the file [1]. 
A new directory entry type can also be used to manage links and prevent dangling pointers [1].

- [1] Unit 5_Part 1_File-system-interface, p.26 - ACYCLIC-GRAPH DIRECTORIES: ACYCLIC-GRAPH DIRECTORIES (CONT.) • Two different names (aliasing) • If dict deletes list dangling pointer Solutions: • Backpointers, so we can delete all pointers Variable size records a problem • Backpointers using a daisy chain organizat

## 18. What do the three digits of chmod 761 mean for owner, group and public?

*concise; answered; judge unsupported: []*

The first digit “7” gives the owner read, write and execute permission. The second digit “6” gives the group read and write permission but not execute. The third digit “1” gives the public only execute permission [1].

- [1] Unit 5_Part 1_File-system-interface, p.38 - ACCESS LISTS AND GROUPS: ACCESS LISTS AND GROUPS • Mode of access: read, write, execute • Three classes of users RWX a) owner access 7 1 1 1 RWX b) group access 6 1 1 0 RWX c) public access 1 0 0 1 • Ask manager to create a group (unique name), say G, and add some 

## 19. How does a UNIX process change its protection domain with the setuid bit, su and sudo?

*concise; answered; judge unsupported: []*

When a file’s setuid bit is on, executing the file changes the process’s user‐id to the file’s owner, thus switching its protection domain [1]. 
The su command temporarily changes the process’s domain to another user after the other user’s password is entered [1]. 
The sudo command prefixes a command so it runs in another user’s domain, provided the original domain has the required privilege or supplies a password [1].

- [1] Unit 5_Part 2_System Protection, p.7 - Domain Implementation (UNIX): Domain Implementation (UNIX) • Domain = user-id • Domain switch accomplished via file system • Each file has associated with it a domain bit (setuid bit) • When file is executed and setuid = on, then user-id is set to owner of the file bein

## 20. In an access matrix, what do the rows and columns represent?

*concise; answered; judge unsupported: []*

Rows represent domains [1]. Columns represent objects [1].

- [1] Unit 5_Part 2_System Protection, p.10 - Access Matrix: Access Matrix • View protection as a matrix (access matrix) • Rows represent domains • Columns represent objects • Access(i, j) is the set of operations that a process executing in Domaini can invoke on Objectj

