# Evidence for eval/questions.jsonl

Labels 1-20 (Stage 1) were taken from the **extracted slide text** of `samples/` (cleaned pages, via `load_document`),
not from search output. The phrase is quoted from the page; the page is the 1-based PDF page.
Questions 2, 5 and 9 are the three whose answer spans two consecutive pages.

| # | file | page(s) | exact answering phrase |
|---|---|---|---|
| 1 | Unit 1_Part 1_Introduction & OS Structure | 12 | "OS has two parts. (1) Kernel is an active part of an OS ... (2) Shell is called as the command interpreter." |
| 2 | Unit 1_Part 1_Introduction & OS Structure | **14, 15** | p.14: "Following are the five services provided by operating systems to the convenience of the users. 1. Program Execution 2. I/O Operations 3. File System Manipulation"; p.15: "4. Communications ... 5. Error Detection" |
| 3 | Unit 1_Part 1_Introduction & OS Structure | 43 | "A computer operates in two modes: User mode and Kernel mode ... System calls refer to these requests." |
| 4 | Unit 1_Part 2_ Process management | 40 | "A Dispatcher is that module of the operating system which gives control of the CPU to the process ... It involves three steps: First, it performs Context switching; Second, Switching to user mode; Finally, Jumping to the proper location in the user program" |
| 5 | Unit 1_Part 2_ Process management | **75, 76** | p.75: "With decreasing value of time quantum, Number of context switch increases, Response time decreases, Chances of starvation decreases"; p.76: "With increasing value of time quantum, Number of context switch decreases, Response time increases, Chances of starvation increases" |
| 6 | Unit 1_Part 2_ Process management | 34 | "fork : A parent process uses fork to create a new child process ... wait : The parent may use wait to suspend execution until a child terminates." |
| 7 | Unit 1_Part 2_ Process management | 115 | "The one to one model creates a separate kernel thread to handle each and every user thread." |
| 8 | Unit 2_Process Synchronization_Deadlock | 6 | "1. Mutual Exclusion ... 2. Progress ... 3. Bound Waiting" (Rules for Critical Section) |
| 9 | Unit 2_Process Synchronization_Deadlock | **11, 12** | p.11: "Binary semaphores can take on one of two values, 0 or 1."; p.12: "Counting semaphores can take on any integer value, and are usually used to count the number remaining of some limited resource." |
| 10 | Unit 2_Process Synchronization_Deadlock | 44 | "If a cycle is being formed in a Resource allocation graph where all the resources have the single instance then the system is deadlocked." |
| 11 | Unit 3_Memory management | 22 | "The best-fit algorithm performed the best of the three algorithms, as it was the only algorithm to meet all the memory requests." |
| 12 | Unit 3_Memory management | 43 | "We can employ TLB (translation look-aside buffer), a particular, tiny, fast look-up hardware cache if the page table has a significant number of entries." |
| 13 | Unit 3_Memory management | 48 | "... using FIFO ... Number of Page Hits = 8, Number of Page Faults = 12" |
| 14 | Unit 4_Storage management_ Disk Schduling | 10 (duplicate: 35) | "Seek time= (82-50) + (170-82) + (170-43) + (140-43) + (140-24) + (24-16) + (190-16) = 642" |
| 15 | Unit 4_Storage management_ Disk Schduling | 14 (duplicate: 39) | "Advantages: disk response time is less. More efficient than FCFS. Disadvantages: Less speed of algorithm execution. Starvation can be seen." |
| 16 | Unit 5_Part 1_File-system-interface | 45 | "An allocation method refers to how disk blocks are allocated for files: Contiguous allocation, Linked allocation, Indexed allocation" |
| 17 | Unit 5_Part 1_File-system-interface | 26 | "If dict deletes list dangling pointer. Solutions: Backpointers ... Entry-hold-count solution ... Link - another name (pointer) to an existing file" |
| 18 | Unit 5_Part 1_File-system-interface | 38 | "owner access 7 (1 1 1), group access 6 (1 1 0), public access 1 (0 0 1) ... chmod 761 game" |
| 19 | Unit 5_Part 2_System Protection | 7 | "Each file has associated with it a domain bit (setuid bit) ... su command temporarily switches to another user's domain ... sudo command prefix executes specified command in another domain" |
| 20 | Unit 5_Part 2_System Protection | 10 | "Rows represent domains. Columns represent objects." |

## Notes
- **Unit 4 duplicates:** the PDF contains its own slides 2-26 a second time as 27-51 (verbatim). Questions 14 and 15
  therefore list the duplicate in `equivalent_pages`: a result covering either copy is a hit, and these two are not
  counted as multi-page questions. (Harness field added before the first run; see NOTES.md.)
- **Distribution:** Unit 1 Part 1: 3, Unit 1 Part 2: 4, Unit 2: 3, Unit 3: 3, Unit 4: 2, Unit 5 Part 1: 3, Unit 5 Part 2: 2.
- **No labelled page is flagged `needs_ocr`** (flagged pages: Unit 2 p.22/40/42, Unit 3 p.26/50-55, Unit 5-1 p.61, Unit 5-2 p.11/28).
- No cross-file questions. None of the three Step 5 questions is reused.
- Wording follows how a student would ask; some questions share words with the slide title, which is realistic
  for exam revision but means the set is not adversarial.

## Stage 2 additions (2026-10-15): ids 21-65

Written by the assistant from the cleaned extracted text of `samples/` (not from search output), then checked by a
script: every phrase below was found (whitespace/case-insensitive) on its labelled page, and every labelled page has
a phrase. Split rule: `eval/QUESTIONS_FORMAT.md`.

**Please spot-check these 10 against the PDFs** (mix of single-page, multi-page, cross-file, duplicate-page and
unanswerable): 23, 25, 29, 35, 39, 44, 46, 50, 54, 58.

| id | split | question | file > page: exact answering phrase |
|---|---|---|---|
| 21 | test | What are the four components of a computer system? | Unit 1_Part 1_Introduction & OS Structure > **p.11**: "Computer system can be divided into four components" |
| 22 | test | Besides user services, which three services does the OS provide to keep the system itself running efficiently? | Unit 1_Part 1_Introduction & OS Structure > **p.16**: "three services provided by operating systems for ensuring the efficient operation of the system itself" |
| 23 (spot-check) | test | What is a real-time operating system, what types exist and what are its advantages? | Unit 1_Part 1_Introduction & OS Structure > **p.37**: "Types of Real Time operating system are"<br>Unit 1_Part 1_Introduction & OS Structure > **p.38**: "Advantages of RTOS" |
| 24 | dev | What does fork return in the parent process, in the child process and on failure? | Unit 1_Part 2_ Process management > **p.35**: "If the return value is 0 the program executes in the new child process" |
| 25 (spot-check) | test | Using exponential averaging with alpha 0.5, what is the predicted burst time for the fifth process? | Unit 1_Part 2_ Process management > **p.63**: "= 6.875 units" |
| 26 | test | What is the convoy effect in FCFS CPU scheduling? | Unit 1_Part 2_ Process management > **p.48**: "smaller processes have to wait for a long time for longer processes to release the CPU" |
| 27 | test | What are the five basic states a process goes through from creation to termination? | Unit 1_Part 2_ Process management > **p.9**: "The minimum number of states is five"<br>Unit 1_Part 2_ Process management > **p.10**: "Completion or termination" |
| 28 | test | What happens to the whole process when a user-level thread performs a blocking operation, compared with a kernel-level thread? | Unit 1_Part 2_ Process management > **p.108**: "if one user-level thread performs a blocking operation then the entire process will be blocked" |
| 29 (spot-check) | test | What is the minimum number of units of a resource that guarantees no deadlock for n processes? | Unit 2_Process Synchronization_Deadlock > **p.30**: "One more than maximum number of units of resource R that ensures deadlock" |
| 30 | dev | How can the circular wait condition be eliminated to prevent deadlock? | Unit 2_Process Synchronization_Deadlock > **p.36**: "imposing a total ordering on all of the resource types" |
| 31 | test | Which data structures (Available, Max, Allocation, Need) does the Banker's algorithm maintain and what do they mean? | Unit 2_Process Synchronization_Deadlock > **p.48**: "Need[i,j] = Max[i,j] - Allocafion[i,j]" |
| 32 | test | What is the difference between a safe state and an unsafe state? | Unit 2_Process Synchronization_Deadlock > **p.38**: "An unsafe state may not be deadlocked" |
| 33 | test | In the first and second readers-writers problems, who can starve? | Unit 2_Process Synchronization_Deadlock > **p.17**: "A solution to this problem can lead to starvation of the writers" |
| 34 | test | What are the advantages and disadvantages of dynamic partitioning? | Unit 3_Memory management > **p.16**: "This scheme also suffers from external fragmentation" |
| 35 (spot-check) | test | For a logical address space of eight pages of 1024 words mapped onto 32 frames, how many bits are in the logical and physical addresses? | Unit 3_Memory management > **p.41**: "13 bits are required for the logical address"<br>Unit 3_Memory management > **p.42**: "15 bits are required for the physical address" |
| 36 | dev | What does the modified (dirty) bit in a page table entry indicate? | Unit 3_Memory management > **p.33**: "Sometimes this modified bit is also called the Dirty bit" |
| 37 | test | How many page faults does LRU page replacement give for the reference string with three frames? | Unit 3_Memory management > **p.49**: "Number of Page Faults = 13" |
| 38 | test | Why is the SCAN disk scheduling algorithm called the elevator algorithm? | Unit 4_Storage management_ Disk Schduling > **p.15**: "this algorithm is also known as the "Elevator Algorithm""<br>Unit 4_Storage management_ Disk Schduling > **p.40**: "Elevator Algorithm" |
| 39 (spot-check) | test | What is the total seek time for C-LOOK on the request sequence 82, 170, 43, 140, 24, 16, 190 with the head at 50? | Unit 4_Storage management_ Disk Schduling > **p.25**: "(190-50) + (190-16) + (43-16) =341"<br>Unit 4_Storage management_ Disk Schduling > **p.50**: "=341" |
| 40 | test | What is the difference between mandatory and advisory file locking? | Unit 5_Part 1_File-system-interface > **p.9**: "Advisory – processes can find status of locks and decide what to do" |
| 41 | test | What are the advantages and drawbacks of contiguous allocation of disk blocks? | Unit 5_Part 1_File-system-interface > **p.46**: "Wasteful of space (dynamic storage-allocation problem)" |
| 42 | dev | How do UNIX file system semantics differ from AFS session semantics for shared files? | Unit 5_Part 1_File-system-interface > **p.36**: "AFS has session semantics" |
| 43 | test | What is the principle of least privilege? | Unit 5_Part 2_System Protection > **p.5**: "Programs, users and systems should be given just enough privileges to perform their tasks" |
| 44 (spot-check) | test | How do access lists for objects differ from capability lists for domains when implementing the access matrix? | Unit 5_Part 2_System Protection > **p.18**: "Access lists for objects"<br>Unit 5_Part 2_System Protection > **p.19**: "Each Row = Capability List"<br>Unit 5_Part 2_System Protection > **p.20**: "Capability list for domains" |
| 45 | test | How does Java protect privileged operations using protection domains and stack inspection? | Unit 5_Part 2_System Protection > **p.27**: "the stack is inspected to ensure the operation can be performed by the library" |
| 46 (spot-check) | test | What is a race condition and how can it be avoided? | Unit 1_Part 1_Introduction & OS Structure > **p.17**: "A race condition occurs when multiple processes or threads access a shared resource simultaneously"<br>Unit 2_Process Synchronization_Deadlock > **p.5**: "We can avoid it if we treat the critical section as an atomic instruction" |
| 47 | test | What is a semaphore and how is it used for synchronization between processes? | Unit 1_Part 2_ Process management > **p.15**: "Semaphore: A variable that manages several processes' access to a shared resource"<br>Unit 2_Process Synchronization_Deadlock > **p.10**: "It uses two atomic operations, 1)wait, and 2) signal" |
| 48 | dev | How does starvation arise in round robin CPU scheduling and in shortest seek time first disk scheduling? | Unit 1_Part 2_ Process management > **p.74**: "It leads to starvation for processes with larger burst time"<br>Unit 4_Storage management_ Disk Schduling > **p.14**: "Starvation can be seen"<br>Unit 4_Storage management_ Disk Schduling > **p.39**: "Starvation can be seen" |
| 49 | test | What is protection in an operating system and how does an access matrix represent it? | Unit 1_Part 1_Introduction & OS Structure > **p.24**: "Protection refers to a mechanism for controlling access by programs, processes, or users"<br>Unit 5_Part 2_System Protection > **p.10**: "Columns represent objects" |
| 50 (spot-check) | test | What memory-management activities is the OS responsible for, and how does paging turn a logical address into a physical address? | Unit 1_Part 1_Introduction & OS Structure > **p.19**: "Keep track of which parts of memory are currently being used and by whom"<br>Unit 3_Memory management > **p.27**: "A physical address is generated which also contains two parts : frame number and offset" |

### Unanswerable (abstention) questions

Each one's key term was searched for in every extracted page of all 7 PDFs and found on none. Most are
deliberately close to covered topics (hard negatives); 60 and 65 are off-topic controls.

| id | split | question | why the notes do not answer it |
|---|---|---|---|
| 51 | test | What is Belady's anomaly in FIFO page replacement? | FIFO page replacement is on Unit 3 p.48, but Belady's anomaly is never mentioned |
| 52 | test | What is thrashing and how does the working-set model prevent it? | no slide mentions thrashing or the working-set model |
| 53 | test | How does copy-on-write make fork faster? | fork is on Unit 1-2 p.34-36, copy-on-write is never mentioned |
| 54 (spot-check) | test | What is priority inversion and how does priority inheritance solve it? | priority scheduling is covered, priority inversion/inheritance are not |
| 55 | test | How does a journaling file system recover after a crash? | no slide mentions journaling |
| 56 | test | What is an inverted page table? | page tables are covered, inverted page tables are not |
| 57 | test | How do semaphores solve the producer-consumer bounded-buffer problem? | semaphores and readers-writers/dining philosophers are covered; producer-consumer/bounded buffer is not |
| 58 (spot-check) | test | What is a microkernel and how does it differ from a monolithic kernel? | the contents slide lists 'Kernel' and 'OS Structure' (slides 60-81) but the PDF ends at page 48; no microkernel/monolithic text |
| 59 | test | How does the test-and-set instruction implement a lock? | Unit 2 p.9 says hardware offers locks, but test-and-set is never described |
| 60 | test | Who proposed the theory of general relativity? | off-topic control question |
| 61 | dev | How does the second-chance (clock) page replacement algorithm work? | only optimal, FIFO and LRU are covered |
| 62 | dev | Why do solid-state drives have no seek time, unlike magnetic disks? | magnetic disks are covered, SSDs are not |
| 63 | dev | What is the sleeping barber problem? | classic problems covered: dining philosophers, readers-writers only |
| 64 | dev | How does multilevel feedback queue scheduling move processes between queues? | multilevel queue is covered (Unit 1-2 p.88-93), feedback queues are not |
| 65 | dev | What is the average time complexity of quicksort? | off-topic control question |

### Counts

- All 65: 50 answerable (12 multi-page, 5 cross-file), 15 unanswerable.
- dev 30: 25 answerable (4 multi-page, 1 cross-file), 5 unanswerable. test 35: 25 answerable (8 multi-page, 4 cross-file), 10 unanswerable.
- New questions per file (21-45): Unit 1-1: 3, Unit 1-2: 5, Unit 2: 5, Unit 3: 4, Unit 4: 2, Unit 5-1: 3, Unit 5-2: 3; cross-file 46-50.
- No labelled page is flagged `needs_ocr`.

## Harder paraphrased questions (2026-10-15): ids 66-81

Written to avoid the words of the labelled slide's title/headings (checked by script: content words longer than
3 letters vs the page's detected headings and first line; the last column lists any overlap that remained).
Phrases script-verified on their pages as above. Split: even id -> dev, odd id -> test (8 each).

| id | split | question | file > page: exact answering phrase | title-word overlap |
|---|---|---|---|---|
| 66 | dev | What are the always-running background helpers that start at boot, such as print servers, usually called? | Unit 1_Part 1_Introduction & OS Structure > **p.48**: "Constantly running system-program processes are known as services, subsystems, or daemons" | none |
| 67 | test | Roughly what share of desktop machines worldwide run the Mac's software, and why is it smaller than its main competitor's? | Unit 1_Part 1_Introduction & OS Structure > **p.8**: "One reason for this is that Apple computers tend to be more expensive" | none |
| 68 | dev | Why is saving one task's registers and loading another's considered wasted time, and how long does it typically take? | Unit 1_Part 2_ Process management > **p.30**: "Typical speeds range from 1 to 1000 microseconds" | none |
| 69 | test | Which component temporarily moves a job out of RAM to reduce how many jobs compete for the processor, and afterwards brings it back? | Unit 1_Part 2_ Process management > **p.23**: "This scheme is called swapping" | none |
| 70 | dev | What happens to a time-slice based policy when the slice is made extremely large? | Unit 1_Part 2_ Process management > **p.77**: "When time quantum tends to infinity, Round Robin Scheduling becomes FCFS" | none |
| 71 | test | What are the two ways to kill a lightweight unit of execution before it completes its work? | Unit 1_Part 2_ Process management > **p.119**: "Deferred cancellation allows the target thread to periodically check if it should be cancelled" | none |
| 72 | dev | How can five diners who share utensils be seated and ordered so that nobody waits forever? | Unit 2_Process Synchronization_Deadlock > **p.15**: "The maximum number of philosophers on the table should not exceed four" | none |
| 73 | test | Can a single job ever end up stuck waiting on itself, and can two threads inside one job block each other this way? | Unit 2_Process Synchronization_Deadlock > **p.28**: "It is not possible to have a deadlock involving only one single process"<br>Unit 2_Process Synchronization_Deadlock > **p.28**: "deadlock is not possible between two threads in a process" | none |
| 74 | dev | Once a circular hold among jobs has been detected, how can it be broken by killing jobs or taking things away from them? | Unit 2_Process Synchronization_Deadlock > **p.57**: "There are two options for breaking a deadlock"<br>Unit 2_Process Synchronization_Deadlock > **p.58**: "Abort all deadlocked processes"<br>Unit 2_Process Synchronization_Deadlock > **p.59**: "Selecting a victim" | none |
| 75 | test | Why does shuffling all the free holes into one place make the machine slow? | Unit 3_Memory management > **p.18**: "the CPU will remain idle for all this time" | none |
| 76 | dev | Which flag in a translation-table row says whether the requested block is resident in main memory, and what is it called when it is not? | Unit 3_Memory management > **p.32**: "In case it is not present, that is called Page Fault" | none |
| 77 | test | If an address has 22 bits and every location holds 2 bytes, how big is the memory? | Unit 3_Memory management > **p.39**: "= 8 MB" | none |
| 78 | dev | What determines how much data a traditional hard drive can store? | Unit 4_Storage management_ Disk Schduling > **p.6**: "The storage capacity of a traditional disk drive is equal to the number of heads"<br>Unit 4_Storage management_ Disk Schduling > **p.31**: "The storage capacity of a traditional disk drive is equal to the number of heads" | none |
| 79 | test | Why does hashing names speed up lookups in a folder, and what problem does it introduce? | Unit 5_Part 1_File-system-interface > **p.58**: "collisions – situations where two file names hash to the same location" | none |
| 80 | dev | In what ways can a permission that was granted earlier be taken back, and how do keys make this possible? | Unit 5_Part 2_System Protection > **p.24**: "Revocation – create new master key" | none |
| 81 | test | Which policies, both for the processor and for the hard-drive arm, handle jobs strictly in the order they show up, and what is their weakness? | Unit 1_Part 2_ Process management > **p.45**: "It schedules according to the arrival time of the process"<br>Unit 1_Part 2_ Process management > **p.48**: "Throughput is not efficient"<br>Unit 4_Storage management_ Disk Schduling > **p.9**: "The requests coming to the disk are arranged in a proper sequence as they arrive"<br>Unit 4_Storage management_ Disk Schduling > **p.11**: "Not so efficient"<br>Unit 4_Storage management_ Disk Schduling > **p.34**: "arranged in a proper sequence as they arrive"<br>Unit 4_Storage management_ Disk Schduling > **p.36**: "Not so efficient" | none |
