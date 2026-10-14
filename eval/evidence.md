# Evidence for eval/questions.jsonl

Every label was taken from the **extracted slide text** of `samples/` (cleaned pages, via `load_document`),
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
