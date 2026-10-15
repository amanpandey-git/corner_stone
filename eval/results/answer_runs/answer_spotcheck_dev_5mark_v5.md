# Answers for manual spot check - split `dev`

Check each: is every sentence supported by the cited slide? Is anything important missing? Note disagreements with the judge in NOTES.md.

## 1. What are the two parts of an operating system and what does each one do?

*5-mark; answered; judge unsupported: []*

Operating system components are divided into two parts: the kernel and the shell [1].

- The kernel is the active part of the OS that runs continuously and can interact directly with hardware [1].
- It includes programs such as device drivers, DLL files, and system files that manage low‐level operations [1].
- The shell is the command interpreter that provides a set of programs for users to interact with application programs [1].
- It is responsible for executing the instructions (commands) given to the OS [1].

- [1] Unit 1_Part 1_Introduction & OS Structure, p.12 - Components of a Computer System: Components of a Computer System Components of OS: OS has two parts. (1) Kernel is an active part of an OS i.e., it is the part of OS running at all times. It is a program which can interact with the hardware. Ex: Device driver, .dll files, 

## 2. Which five services does an operating system provide for the convenience of its users?

*5-mark; answered; judge unsupported: []*

Operating system services are functions that the OS provides to make using the computer convenient for users [1].

- Program execution, allowing users to run programs by handling memory allocation, deallocation and CPU scheduling [1].
- I/O operations, managing input and output so programs can receive data and produce results [1].
- File system manipulation, enabling programs to read from and write to files as needed [1].
- Resource allocation, distributing hardware and software resources among multiple users or jobs [2].
- Protection, controlling access to system resources and preventing interference between processes [2].

- [1] Unit 1_Part 1_Introduction & OS Structure, pp.13-14 - Operating System Services: A View of Operating System Services Operating System Services Following are the five services provided by operating systems to the convenience of the users. 1. Program Execution The purpose of computer systems is to allow the user to execut
- [2] Unit 1_Part 1_Introduction & OS Structure, p.16 - Operating System Services: Operating System Services Following are the three services provided by operating systems for ensuring the efficient operation of the system itself. 1. Resource allocation When multiple users are logged on the system or multiple jobs are run

## 3. What are the user mode and kernel mode, and what is a system call?

*5-mark; answered; judge unsupported: []*

- User mode is the execution mode where a program runs, and it cannot directly access hardware resources [1].
- Kernel mode is the privileged execution mode that can interact with hardware and system resources, entered when a program requests such services [1].
- A system call is a request from a program to the operating system’s kernel for a service or resource [2].
- System calls serve as the method for user‐level programs to request operating‐system services via the API [2].
- The shell acts as an intermediary that interprets user commands and makes the appropriate system calls [2].

- [1] Unit 1_Part 1_Introduction & OS Structure, p.43 - What is a System Call: What is a System Call A computer operates in two modes: User mode and Kernel mode. The execution of a program is in the user mode. When the program requires RAM or a hardware resource, it sends a request to the kernel and the mode changes f
- [2] Unit 1_Part 1_Introduction & OS Structure, p.44 - What is a System Call: shell: acts as an intermediary b/w user and system call. Interpret user command and makes system calls. System Calls ➢A system call is a method for a computer program to request a service from the kernel of the operating system on which it 

## 4. What does the dispatcher do and which steps does it involve?

*5-mark; answered; judge unsupported: []*

- The dispatcher is the OS module that gives control of the CPU to a process after the short‐term scheduler selects it[1].
- It performs a context‐switch to save the state of the currently running process and load the state of the chosen process[1].
- It switches the CPU from kernel mode to user mode so the process can run in its own protection domain[1].
- It jumps to the correct location in the user program to restart execution of the process[1].

- [1] Unit 1_Part 2_ Process management, p.40 - Dispatcher: Dispatcher A Dispatcher is that module of the operating system which gives control of the CPU to the process. Short term scheduler only decides which process to allocate to CPU. Whereas the dispatcher actually allocates the CPU to that proc

## 5. How does the size of the time quantum affect context switches, response time and starvation in round robin scheduling?

*5-mark; answered; judge unsupported: []*

Round Robin scheduling uses a fixed time quantum to allocate CPU time to each process [5].

- A smaller time quantum increases the number of context switches [1].
- A smaller time quantum decreases response time [1].
- A smaller time quantum reduces the chances of starvation [1].
- A larger time quantum decreases the number of context switches [2].
- A larger time quantum increases response time [2].
- A larger time quantum raises the chances of starvation [2].

- [5] Unit 1_Part 2_ Process management, p.72 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm In Round Robin Scheduling, ➢CPU is assigned to the process based on FCFS for a fixed amount of time. ➢This fixed amount of time is called as time quantum or time slice. ➢After the time quantum expires, the r
- [1] Unit 1_Part 2_ Process management, p.75 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm Note-01: With decreasing value of time quantum, ➢Number of context switch increases ➢Response time decreases ➢Chances of starvation decreases Thus, smaller value of time quantum is better in terms of respons
- [2] Unit 1_Part 2_ Process management, p.76 - Round Robin Scheduling Algorithm: Round Robin Scheduling Algorithm Note-02: With increasing value of time quantum, ➢Number of context switch decreases ➢Response time increases ➢Chances of starvation increases Thus, higher value of time quantum is better in terms of number o

## 6. Which system calls does a parent use to create a child process and to wait for it to finish?

*5-mark; answered; judge unsupported: []*

- A parent creates a child process with the **fork** system call, which makes the child a copy of the parent [1].
- After forking, the parent can suspend execution until the child terminates using the **wait** system call [1][3].

- [1] Unit 1_Part 2_ Process management, p.34 - Process Creation: Process Creation The following system calls are used for basic process management. fork : A parent process uses fork to create a new child process. The child process is a copy of the parent. After fork, both parent and child executes the sa
- [3] Unit 1_Part 2_ Process management, p.37 - Wait: Wait The wait system call blocks the caller until one of its child process terminates. If the caller doesn’t have any child processes, wait returns immediately without blocking the caller. Using wait the parent can obtain the exit status of

