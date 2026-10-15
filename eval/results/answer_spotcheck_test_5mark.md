# Answers for manual spot check - split `test`

Check each: is every sentence supported by the cited slide? Is anything important missing? Note disagreements with the judge in NOTES.md.

## 21. What are the four components of a computer system?

*5-mark; answered; judge unsupported: []*

The computer system is organized into four main components. 

- **Hardware** provides basic computing resources such as the CPU, memory, and I/O devices [1]. 
- **Operating system** controls and coordinates the use of hardware among various applications and users [1]. 
- **Application programs** define how system resources are used to solve user problems, e.g., word processors, compilers, web browsers, database systems, video games [1]. 
- **Users** include people, machines, and other computers that interact with the system [1]. 

These four components together form the structure of a computer system.

- [1] Unit 1_Part 1_Introduction & OS Structure, p.11 - Computer system can be divided into four components: Computer system can be divided into four components • Hardware – provides basic computing resources, ex. CPU, memory, I/O devices • Operating system - Controls and coordinates use of hardware among various applications and users • Applicati

## 22. Besides user services, which three services does the OS provide to keep the system itself running efficiently?

*5-mark; answered; judge unsupported: []*

The operating system supplies internal services that maintain efficient system operation. 

- It allocates resources such as CPU time, memory and devices to multiple users or jobs [1]. 
- It records resource usage for each user, enabling accounting or usage statistics [1]. 
- It enforces protection so that concurrent processes cannot interfere with each other or the OS, and it handles user authentication for security [1]. 

These services ensure the system runs smoothly and securely.

- [1] Unit 1_Part 1_Introduction & OS Structure, p.16 - Operating System Services: Operating System Services Following are the three services provided by operating systems for ensuring the efficient operation of the system itself. 1. Resource allocation When multiple users are logged on the system or multiple jobs are run

## 23. What is a real-time operating system, what types exist and what are its advantages?

*5-mark; answered; judge unsupported: [2]*

A real‐time operating system (RTOS) is designed to handle time‐sensitive tasks where processing must finish within a strict deadline, otherwise the result may be useless or cause huge loss [1].

- An RTOS ensures that each job is completed before its deadline [1].
- It is used in applications such as military missile dropping, where precise timing is critical [1].
- The main types of RTOS are Hard Real‐Time, Soft Real‐Time, and Firm Real‐Time operating systems [1].

The notes do not list specific advantages of real‐time operating systems. NOT_IN_NOTES

- [1] Unit 1_Part 1_Introduction & OS Structure, p.37 - An Operating system, which includes: In Real-Time Systems, each job carries a certain A Real-Time Operating System (RTOS) is designed to handle time-sensitive tasks where processing must occur within a strict deadline. deadline within which the job is supposed to be completed,

## 25. Using exponential averaging with alpha 0.5, what is the predicted burst time for the fifth process?

*5-mark; answered; judge unsupported: []*

The exponential averaging predicts the fifth process’s burst time as 6.875 units [2].

- [2] Unit 1_Part 2_ Process management, p.63 - Example: Example Predicted Burst Time for 4th Process- Predicted burst time for 4th process = α x Actual burst time of 3rd process + (1-α) x Predicted burst time for 3rd process = 0.5 x 6 + 0.5 x 7.5 = 3 + 3.75 = 6.75 units Predicted Burst Time for 

## 26. What is the convoy effect in FCFS CPU scheduling?

*5-mark; answered; judge unsupported: []*

The convoy effect is a drawback of the First‐Come‐First‐Serve (FCFS) scheduling algorithm. 

- It occurs when processes with long CPU bursts arrive before processes with short bursts [1]. 
- The short‐burst processes must wait for the long‐burst processes to finish using the CPU [1]. 
- This waiting causes the short processes to experience long delays despite arriving later [1]. 
- The effect can significantly reduce overall system responsiveness and throughput [1]. 

Thus, the convoy effect describes how long jobs can block shorter ones in FCFS, leading to inefficient CPU utilization.

- [1] Unit 1_Part 2_ Process management, p.48 - First Come First Serve: First Come First Serve Advantages of FCFS : • Simple • Easy, useful and understandable Convoy Effect In convoy effect, •Consider processes with higher burst time arrived before the processes with smaller burst time. •Then, smaller processes

## 27. What are the five basic states a process goes through from creation to termination?

*5-mark; answered; judge unsupported: []*

The process moves through five basic states from creation to termination. 

- **New** – a program entered into main memory becomes a new process [2]. 
- **Ready** – the newly created process enters the ready queue and waits for CPU assignment [2][5]. 
- **Running** – the scheduler selects a ready process to execute on the CPU [1][5]. 
- **Block or Wait** – while running, a process may move to the block/wait state when it needs a resource or user input [1]. 
- **Termination** – after completing execution, the process enters the termination state and its PCB is deleted [1][5]. 

These five states describe the complete lifecycle of a process.

- [2] Unit 1_Part 2_ Process management, pp.8-9 - Process States: Process States Process States The process, from its creation to completion, passes through various states. The minimum number of states is five. The names of the states are not standardized although the process may be in one of the followin
- [5] Unit 1_Part 2_ Process management, p.31 - Operation on Processes: Operation on Processes 1. Creation : Once the process is created, it will be ready and come into the ready queue (main memory) and will be ready for the execution. 2. Scheduling : Out of the many processes present in the ready queue, the Op
- [1] Unit 1_Part 2_ Process management, p.10 - Process States: Process States 3. Running : One of the processes from the ready state will be chosen by the OS depending upon the scheduling algorithm 4. Block or wait : From the Running state, a process can make the transition to the block or wait state d

## 28. What happens to the whole process when a user-level thread performs a blocking operation, compared with a kernel-level thread?

*5-mark; answered; judge unsupported: []*

User‐level and kernel‐level threads differ in how a blocking operation affects their process. 

- A blocking operation by a user‐level thread blocks the entire process [1]. 
- A blocking operation by a kernel‐level thread does not block the whole process; other threads can continue executing [1]. 
- User‐level threads are implemented by a thread library and lack kernel support [1][2]. 
- Kernel‐level threads are recognized and managed by the operating system, requiring hardware support [1]. 

Thus, only kernel‐level threads allow part of a process to keep running when one thread blocks.

- [1] Unit 1_Part 2_ Process management, p.108 - Types of Thread: Types of Thread User Level threads Kernel Level Threads These threads are implemented by users. These threads are implemented by Operating systems These threads are not recognized by operating systems, These threads are recognized by operat
- [2] Unit 1_Part 2_ Process management, p.107 - Types of Thread: Types of Thread There are two types of threads: User threads are above the kernel and without kernel support. These are the threads that application programmers use in their programs. Kernel threads are supported within the kernel of the OS

## 29. What is the minimum number of units of a resource that guarantees no deadlock for n processes?

*5-mark; answered; judge unsupported: []*

The minimum number of units of a resource that guarantees no deadlock for n processes is one more than the maximum number that could cause deadlock. 

- The maximum number of units that can cause deadlock is the sum of each process’s maximum demand minus the number of processes: ∑ xi – n [2]. 
- Adding one extra unit to this amount ensures that at least one process can obtain all the resources it needs, complete, and release its units [2]. 
- Therefore, the minimum number of units that guarantees a deadlock‐free system is (∑ xi – n) + 1 [2]. 
- This formula applies to any set of processes with known maximum resource requirements x1, x2,..., xn [3]. 

In summary, providing one more resource unit than the worst‐case deadlock‐inducing total prevents deadlock.

- [2] Unit 2_Process Synchronization_Deadlock, p.30 - Maximum Number Of Units That Ensures Deadlock-: Maximum Number Of Units That Ensures Deadlock- Maximum number of units of resource R that ensures deadlock = (x1-1) + (x2-1) + (x3-1) + …. + (xn-1) = ( x1 + x2 + x3 + …. + xn ) – n = ∑xi – n = Sum of max needs of all n processes – n Minimum
- [3] Unit 2_Process Synchronization_Deadlock, p.29 - Important Concept: Important Concept Consider there are n processes in the system P1, P2, P3, …… , Pn where- ▪Process P1 requires x1units of resource R ▪Process P2 requires x2units of resource R ▪Process P3 requires x3units of resource R and so on. In worst c

## 51. What is Belady's anomaly in FIFO page replacement?

*5-mark; abstained: model; judge unsupported: not checked*

Not in your notes.

- [1] Unit 3_Memory management, p.48 - Example: Example Consider the reference string 6, 1, 1, 2, 0, 3, 4, 6, 0, 2, 1, 2, 1, 2, 0, 3, 2, 1, 2, 0 for a memory with three frames and calculate number of page faults by using FIFO (First In First Out) Page replacement algorithms. PAGING Point
- [2] Unit 3_Memory management, p.49 - Example: Example Consider the reference string 6, 1, 1, 2, 0, 3, 4, 6, 0, 2, 1, 2, 1, 2, 0, 3, 2, 1, 2, 0 for a memory with three frames and calculate number of page faults by using LRU (Least Recently Used) Page replacement algorithms. PAGING Point
- [3] Unit 3_Memory management, p.44 - PAGE REPLACEMENT ALGORITHM: PAGE REPLACEMENT ALGORITHM Paging in Operating Systems PAGING Virtual Memory in Operating Systems Demand Paging

## 52. What is thrashing and how does the working-set model prevent it?

*5-mark; abstained: model; judge unsupported: not checked*

Not in your notes.

- [1] Unit 2_Process Synchronization_Deadlock, p.44 - Deadlock Detection using RAG: Deadlock Detection using RAG ➢If a cycle is being formed in a Resource allocation graph where all the resources have the single instance then the system is deadlocked. ➢In Case of Resource allocation graph with multi-instanced resource type
- [2] Unit 2_Process Synchronization_Deadlock, p.41 - Resource-Allocation Graph: Edges in RAG are also of two types, one represents assignment and other represents the wait of a process for a resource.
- [3] Unit 4_Storage management_ Disk Schduling, p.23 - LOOK Disk Scheduling Algorithm: LOOK Disk Scheduling Algorithm Advantages: • Starvation does not occur. • Since the head does not go to the end of the disk, the time is not wasted here. Disadvantage: • The arm has to be conscious to find the last request

