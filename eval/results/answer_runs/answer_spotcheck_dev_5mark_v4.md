# Answers for manual spot check - split `dev`

Check each: is every sentence supported by the cited slide? Is anything important missing? Note disagreements with the judge in NOTES.md.

## 1. What are the two parts of an operating system and what does each one do?

*5-mark; answered; judge unsupported: []*

An operating system is composed of two main parts: the kernel and the shell [1].

- The kernel is the active part of the OS that runs at all times [1].
- It is a program that can interact directly with the hardware [1].
- The shell is the command interpreter of the OS [1].
- It is a set of programs used to interact with application programs [1].
- The shell is responsible for executing the instructions (commands) given to the OS [1].

Together, the kernel provides core system control while the shell offers a user‐level interface for command execution [1].

- [1] Unit 1_Part 1_Introduction & OS Structure, p.12 - Components of a Computer System: Components of a Computer System Components of OS: OS has two parts. (1) Kernel is an active part of an OS i.e., it is the part of OS running at all times. It is a program which can interact with the hardware. Ex: Device driver, .dll files, 

## 2. Which five services does an operating system provide for the convenience of its users?

*5-mark; answered; judge unsupported: [7]*

Operating systems offer several services that make using a computer convenient for users [1].
- They provide a program‐execution environment that handles memory allocation and CPU scheduling for running programs [1].
- They manage input/output operations so programs can receive data and produce results without direct hardware handling [1].
- They support file‐system manipulation, allowing programs to read from and write to files as needed [1].
- They allocate system resources among multiple users or jobs to ensure each has what it needs [2].
- They keep accounting records of resource usage for billing or statistical purposes [2].

These services together create a user‐friendly and efficient computing environment [1].

- [1] Unit 1_Part 1_Introduction & OS Structure, pp.13-14 - Operating System Services: A View of Operating System Services Operating System Services Following are the five services provided by operating systems to the convenience of the users. 1. Program Execution The purpose of computer systems is to allow the user to execut
- [2] Unit 1_Part 1_Introduction & OS Structure, p.16 - Operating System Services: Operating System Services Following are the three services provided by operating systems for ensuring the efficient operation of the system itself. 1. Resource allocation When multiple users are logged on the system or multiple jobs are run

## 3. What are the user mode and kernel mode, and what is a system call?

*5-mark; answered; judge unsupported: [3]*

User mode runs application code while kernel mode runs privileged OS code and handles hardware access [1].

- User mode is where normal programs execute and cannot directly access hardware resources [1].
- Kernel mode is a privileged state that allows the OS to control hardware and manage resources [1].
- A system call is a request from a program in user mode to the kernel for a service such as memory or device access [1][2].
- System calls act as the interface that lets user‐level programs request operating‐system services and cause a switch from user mode to kernel mode [2].
- The shell can interpret user commands and invoke system calls on behalf of programs [2].

System calls enable safe interaction between user programs and the kernel by switching modes as needed [1].

- [1] Unit 1_Part 1_Introduction & OS Structure, p.43 - What is a System Call: What is a System Call A computer operates in two modes: User mode and Kernel mode. The execution of a program is in the user mode. When the program requires RAM or a hardware resource, it sends a request to the kernel and the mode changes f
- [2] Unit 1_Part 1_Introduction & OS Structure, p.44 - What is a System Call: shell: acts as an intermediary b/w user and system call. Interpret user command and makes system calls. System Calls ➢A system call is a method for a computer program to request a service from the kernel of the operating system on which it 

## 4. What does the dispatcher do and which steps does it involve?

*5-mark; answered; judge unsupported: [3, 6]*

The dispatcher is the OS module that gives control of the CPU to a process [1].

- It allocates the CPU to the selected process after the short‐term scheduler makes a decision [1].
- It performs a context‐switch to save the state of the old process and load the state of the new one [1].
- It switches the processor from kernel mode to user mode [1].
- It jumps to the correct location in the user program to restart execution of the process [1].

Thus, the dispatcher completes the final steps that move a process from ready to running state [1].

- [1] Unit 1_Part 2_ Process management, p.40 - Dispatcher: Dispatcher A Dispatcher is that module of the operating system which gives control of the CPU to the process. Short term scheduler only decides which process to allocate to CPU. Whereas the dispatcher actually allocates the CPU to that proc

## 5. How does the size of the time quantum affect context switches, response time and starvation in round robin scheduling?

*5-mark; answered; judge unsupported: []*

Round‐Robin scheduling’s behavior changes with the size of the time quantum [1][2].

- A smaller time quantum increases the number of context switches [1].
- A smaller time quantum reduces the average response time [1].
- A smaller time quantum lowers the chances of starvation [1].
- A larger time quantum decreases the number of context switches [2].
- A larger time quantum raises the average response time [2].
- A larger time quantum raises the chances of starvation [2].

Choosing an appropriate quantum is important because performance depends heavily on its value and it should not be too big or too small [3][4].

Thus, the time quantum directly influences context‐switch frequency, response time, and starvation risk in Round‐Robin scheduling [1][2][3][4].

- [1] Unit 1_Part 2_ Process management, p.75 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm Note-01: With decreasing value of time quantum, ➢Number of context switch increases ➢Response time decreases ➢Chances of starvation decreases Thus, smaller value of time quantum is better in terms of respons
- [2] Unit 1_Part 2_ Process management, p.76 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm Note-02: With increasing value of time quantum, ➢Number of context switch decreases ➢Response time increases ➢Chances of starvation increases Thus, higher value of time quantum is better in terms of number o
- [3] Unit 1_Part 2_ Process management, p.77 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm Note-03: ➢With increasing value of time quantum, Round Robin Scheduling tends to become FCFS Scheduling. ➢When time quantum tends to infinity, Round Robin Scheduling becomes FCFS Scheduling. Note-04: ➢The pe
- [4] Unit 1_Part 2_ Process management, pp.73-74 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm Round Robin Scheduling Algorithm Advantages- ➢It gives the best performance in terms of average response time. ➢It is best suited for time sharing system, client server architecture and interactive system. D

## 6. Which system calls does a parent use to create a child process and to wait for it to finish?

*5-mark; answered; judge unsupported: []*

The parent process creates a child and waits for its termination using specific system calls [1].

- The parent calls **fork** to create a new child process, which is a copy of the parent [1].
- After forking, the child can call **exec** to replace its memory space with a different program, allowing it to run a program different from the parent [1].
- The parent uses **wait** to block until the child process terminates and to obtain the child’s exit status [1][3].
- If the parent has no children, **wait** returns immediately without blocking [3].

These system calls enable the parent to spawn a child process and synchronize with its completion [1].

- [1] Unit 1_Part 2_ Process management, p.34 - Process Creation: Process Creation The following system calls are used for basic process management. fork : A parent process uses fork to create a new child process. The child process is a copy of the parent. After fork, both parent and child executes the sa
- [3] Unit 1_Part 2_ Process management, p.37 - Wait: Wait The wait system call blocks the caller until one of its child process terminates. If the caller doesn’t have any child processes, wait returns immediately without blocking the caller. Using wait the parent can obtain the exit status of

## 7. Which multithreading model gives every user thread its own kernel thread?

*5-mark; answered; judge unsupported: []*

The one‐to‐one model maps each user thread to its own kernel thread[3].

- It creates a separate kernel thread for every user thread[3].
- This mapping gives each user thread its own kernel‐level execution context[3].
- Linux and Windows (95 to XP) implement this one‐to‐one mapping[3].
- The model provides more concurrency than the many‐to‐one model[3].

Thus, the one‐to‐one multithreading model assigns an individual kernel thread to each user thread[3].

- [3] Unit 1_Part 2_ Process management, pp.114-115 - One to One Model: Many to One Model One to One Model ❖The one to one model creates a separate kernel thread to handle each and every user thread. ❖Most implementations of this model place a limit on how many threads can be created. ❖Linux and Windows from 95

## 8. What three requirements must a solution to the critical section problem satisfy?

*5-mark; answered; judge unsupported: [5]*

The solution to the critical‐section problem must satisfy three essential requirements [3].
- Mutual exclusion: only one process may be executing in its critical section at any time [3].
- Progress: if no process is in its critical section, a waiting process must be allowed to enter without indefinite postponement [3].
- Bounded waiting: a limit exists on how many other processes can enter their critical sections before a requesting process is granted entry [3].
These three conditions ensure correct and fair access to shared resources [3].

- [3] Unit 2_Process Synchronization_Deadlock, p.6 - Rules for Critical Section: Rules for Critical Section 1. Mutual Exclusion: Only one process at a time can be executing in their critical section. 2. Progress: If no process is currently executing in their critical section, and one or more processes want to execute th

## 61. How does the second-chance (clock) page replacement algorithm work?

*5-mark; abstained: model; judge unsupported: not checked*

Not in your notes.

- [1] Unit 3_Memory management, p.47 - PAGE REPLACEMENT ALGORITHMS: PAGE REPLACEMENT ALGORITHMS There are three types of Page Replacement Algorithms. They are: • Optimal Page Replacement Algorithm PAGING • First In First Out Page Replacement Algorithm • Least Recently Used (LRU) Page Replacement Algorithm
- [2] Unit 3_Memory management, p.44 - PAGE REPLACEMENT ALGORITHM: PAGE REPLACEMENT ALGORITHM Paging in Operating Systems PAGING Virtual Memory in Operating Systems Demand Paging
- [3] Unit 3_Memory management, p.49 - Example: Example Consider the reference string 6, 1, 1, 2, 0, 3, 4, 6, 0, 2, 1, 2, 1, 2, 0, 3, 2, 1, 2, 0 for a memory with three frames and calculate number of page faults by using LRU (Least Recently Used) Page replacement algorithms. PAGING Point

## 62. Why do solid-state drives have no seek time, unlike magnetic disks?

*5-mark; abstained: model; judge unsupported: not checked*

Not in your notes.

- [1] Unit 4_Storage management_ Disk Schduling, p.14 - Shortest Seek Time First: Shortest Seek Time First Advantages: • In this algorithm, disk response time is less. • More efficient than FCFS. Disadvantages: • Less speed of algorithm execution. • Starvation can be seen.
- [2] Unit 4_Storage management_ Disk Schduling, pp.5-6 - Magnetic Disk: Magnetic Disk Magnetic Disk • One or more platters in the form of disks covered with magnetic media. • Each platter has two working surfaces. • Each working surface is divided into a number of concentric rings called tracks. The collection 
- [3] Unit 4_Storage management_ Disk Schduling, p.4 - Important Terms: Important Terms ▪Seek Time - It is the time taken by the disk arm to locate the desired track. ▪Rotational Latency - The time taken by a desired sector of the disk to rotate itself to the position where it can access the Read/Write heads is

