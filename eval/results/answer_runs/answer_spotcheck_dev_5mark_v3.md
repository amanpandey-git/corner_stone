# Answers for manual spot check - split `dev`

Check each: is every sentence supported by the cited slide? Is anything important missing? Note disagreements with the judge in NOTES.md.

## 1. What are the two parts of an operating system and what does each one do?

*5-mark; answered; judge unsupported: []*

Operating systems consist of two main components that work together to manage the computer. 

- The **kernel** is the active part of the OS that runs continuously and can interact directly with the hardware [1]. 
- It includes low‐level programs such as device drivers, system files and dynamic‐link libraries that control hardware resources [1]. 
- The **shell** is the command interpreter that provides a set of programs for users to interact with application programs [1]. 
- It receives user commands and is responsible for executing those instructions on the OS [1]. 

Together, the kernel handles hardware control while the shell provides the interface for users to issue commands.

- [1] Unit 1_Part 1_Introduction & OS Structure, p.12 - Components of a Computer System: Components of a Computer System Components of OS: OS has two parts. (1) Kernel is an active part of an OS i.e., it is the part of OS running at all times. It is a program which can interact with the hardware. Ex: Device driver, .dll files, 

## 2. Which five services does an operating system provide for the convenience of its users?

*5-mark; answered; judge unsupported: []*

Operating systems offer several services that make using a computer easier for users. 

- Program execution, providing an environment that handles memory allocation and CPU scheduling for running programs [1]. 
- I/O operations, managing input and output devices so programs can receive data and produce results [1]. 
- File system manipulation, enabling programs to create, read, write, and manage files as needed [1]. 
- Resource allocation, distributing hardware and software resources among multiple users or jobs [2]. 
- Protection, controlling access to system resources and ensuring security against interference and unauthorized use [2]. 

These services together create a convenient and efficient computing environment for users.

- [1] Unit 1_Part 1_Introduction & OS Structure, pp.13-14 - Operating System Services: A View of Operating System Services Operating System Services Following are the five services provided by operating systems to the convenience of the users. 1. Program Execution The purpose of computer systems is to allow the user to execut
- [2] Unit 1_Part 1_Introduction & OS Structure, p.16 - Operating System Services: Operating System Services Following are the three services provided by operating systems for ensuring the efficient operation of the system itself. 1. Resource allocation When multiple users are logged on the system or multiple jobs are run

## 3. What are the user mode and kernel mode, and what is a system call?

*5-mark; answered; judge unsupported: [1, 2]*

User mode and kernel mode are two execution states of a computer, and a system call is the mechanism that lets programs move between them. 

- User mode is where ordinary program code runs, isolated from direct hardware access [1]. 
- Kernel mode is the privileged state in which the operating system core can control hardware and manage resources [1]. 
- When a program needs RAM or a hardware resource, it sends a request that causes a switch from user mode to kernel mode [1]. 
- This request is called a system call, which is a method for a program to request a service from the OS kernel [2][3]. 
- The shell acts as an intermediary that interprets user commands and invokes system calls on behalf of programs [2]. 
- After the kernel completes the requested service, the CPU returns to user mode, completing the context switch [1]. 

Thus, user mode isolates applications, kernel mode provides privileged control, and system calls bridge the two.

- [1] Unit 1_Part 1_Introduction & OS Structure, p.43 - What is a System Call: What is a System Call A computer operates in two modes: User mode and Kernel mode. The execution of a program is in the user mode. When the program requires RAM or a hardware resource, it sends a request to the kernel and the mode changes f
- [2] Unit 1_Part 1_Introduction & OS Structure, p.44 - What is a System Call: shell: acts as an intermediary b/w user and system call. Interpret user command and makes system calls. System Calls ➢A system call is a method for a computer program to request a service from the kernel of the operating system on which it 
- [3] Unit 1_Part 1_Introduction & OS Structure, p.45 - System Calls: System Calls • Programming interface to the services provided by the OS • Typically written in a high-level language (C or C++) • Mostly accessed by programs via a high-level Application Program Interface (API) rather than direct system cal

## 4. What does the dispatcher do and which steps does it involve?

*5-mark; answered; judge unsupported: []*

The dispatcher is the OS component that actually gives the CPU to a selected process. 

- It allocates the CPU to the process chosen by the short‐term scheduler [1]. 
- It performs a context‐switch to save the state of the currently running process and load the state of the next process [1]. 
- It switches the processor from kernel mode to user mode so the process can run in its own protection domain [1]. 
- It jumps to the correct location in the user program to restart execution of the process [1]. 

Thus, the dispatcher’s role is to hand over CPU control by executing these three steps.

- [1] Unit 1_Part 2_ Process management, p.40 - Dispatcher: Dispatcher A Dispatcher is that module of the operating system which gives control of the CPU to the process. Short term scheduler only decides which process to allocate to CPU. Whereas the dispatcher actually allocates the CPU to that proc

## 5. How does the size of the time quantum affect context switches, response time and starvation in round robin scheduling?

*5-mark; answered; judge unsupported: []*

Round‐Robin scheduling’s behavior changes with the length of the time quantum. 

- A smaller time quantum increases the number of context switches [1]. 
- A smaller time quantum reduces the average response time [1]. 
- A smaller time quantum lowers the chances of starvation [1]. 
- A larger time quantum decreases the number of context switches [2]. 
- A larger time quantum raises the average response time [2]. 
- A larger time quantum raises the chances of starvation [2]. 

Choosing an appropriate quantum is therefore a trade‐off: it must be neither too short nor too long to balance context‐switch overhead, response time, and starvation risk.

- [1] Unit 1_Part 2_ Process management, p.75 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm Note-01: With decreasing value of time quantum, ➢Number of context switch increases ➢Response time decreases ➢Chances of starvation decreases Thus, smaller value of time quantum is better in terms of respons
- [2] Unit 1_Part 2_ Process management, p.76 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm Note-02: With increasing value of time quantum, ➢Number of context switch decreases ➢Response time increases ➢Chances of starvation increases Thus, higher value of time quantum is better in terms of number o

## 6. Which system calls does a parent use to create a child process and to wait for it to finish?

*5-mark; answered; judge unsupported: []*

The parent creates a child process with the **fork** system call and then waits for the child to finish with the **wait** system call. 

- **fork** creates a new child process that is a copy of the parent [1]. 
- After forking, the parent can call **wait** to block until the child terminates [3]. 
- **wait** returns the PID of the terminated child and can provide its exit status [3]. 

Thus, the parent uses **fork** for creation and **wait** for synchronization.

- [1] Unit 1_Part 2_ Process management, p.34 - Process Creation: Process Creation The following system calls are used for basic process management. fork : A parent process uses fork to create a new child process. The child process is a copy of the parent. After fork, both parent and child executes the sa
- [3] Unit 1_Part 2_ Process management, p.37 - Wait: Wait The wait system call blocks the caller until one of its child process terminates. If the caller doesn’t have any child processes, wait returns immediately without blocking the caller. Using wait the parent can obtain the exit status of

## 7. Which multithreading model gives every user thread its own kernel thread?

*5-mark; answered; judge unsupported: []*

The one‐to‐one model maps each user thread to a separate kernel thread. [3]

- [3] Unit 1_Part 2_ Process management, pp.114-115 - One to One Model: Many to One Model One to One Model ❖The one to one model creates a separate kernel thread to handle each and every user thread. ❖Most implementations of this model place a limit on how many threads can be created. ❖Linux and Windows from 95

## 8. What three requirements must a solution to the critical section problem satisfy?

*5-mark; answered; judge unsupported: []*

The solution to the critical‐section problem must meet three essential requirements.

- **Mutual exclusion**: only one process may be executing in its critical section at any time [3]. 
- **Progress**: if no process is in its critical section and some processes wish to enter, the decision to allow entry must be made without indefinite postponement [3]. 
- **Bounded waiting**: a requesting process will eventually be granted entry, and only a limited number of other processes may enter before it [3].

These three conditions ensure correct and fair synchronization of concurrent processes.

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

