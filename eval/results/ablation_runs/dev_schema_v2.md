# Retrieval evaluation - split `dev` - schema v2 (no ranking change expected)

Generated 2026-10-15 by `eval/retrieval_eval.py --split dev`. Index: 7 documents, 328 vectors, model `BAAI/bge-small-en-v1.5`, ef_search=50. Nothing was tuned on the test split.

## Summary

| metric | value |
|---|---|
| scored questions | 33 |
| **hit@5** | **0.879** (29/33) |
| **MRR** (top-10) | **0.816** |
| multi-page questions | 5: 6/11 labelled pages found in top 5 |
| cross-file questions | 1: 0 with every file in top 5 |
| end-to-end search latency p50 / p95 | 46 ms / 63 ms (query embedding + HNSW + SQLite, k=10) |
| unanswerable questions in split | 5 (not scored here; Phase 2 abstention) |

Definitions: a result covers a labelled page if it is from that target's file and the page lies inside the chunk's page range. hit@5 = any labelled page covered in the top 5. MRR = mean of 1/rank of the first covering result (top 10, else 0).

## Excluded from scoring

The three questions asked by hand in Step 5 (their results were shown to the author before evaluation):

- What are the four necessary conditions for deadlock?
- What is the difference between a process and a thread?
- How does paging avoid external fragmentation?

## Per question

| id | question | expected | rank | hit@5 | top result |
|---|---|---|---|---|---|
| 1 | What are the two parts of an operating system and what does each one do? | Unit 1_Part 1_Introduction & OS Structure.pdf p.12 | 1 | yes | Unit 1_Part 1_Introduction & OS Structure.pdf p.11-12 |
| 2 | Which five services does an operating system provide for the convenience of its users? | Unit 1_Part 1_Introduction & OS Structure.pdf p.14,15 [1/2 pages in top 5] | 1 | yes | Unit 1_Part 1_Introduction & OS Structure.pdf p.13-14 |
| 3 | What are the user mode and kernel mode, and what is a system call? | Unit 1_Part 1_Introduction & OS Structure.pdf p.43 | 1 | yes | Unit 1_Part 1_Introduction & OS Structure.pdf p.43 |
| 4 | What does the dispatcher do and which steps does it involve? | Unit 1_Part 2_ Process management.pdf p.40 | 1 | yes | Unit 1_Part 2_ Process management.pdf p.40 |
| 5 | How does the size of the time quantum affect context switches, response time and starvation in round robin scheduling? | Unit 1_Part 2_ Process management.pdf p.75,76 [2/2 pages in top 5] | 1 | yes | Unit 1_Part 2_ Process management.pdf p.75 |
| 6 | Which system calls does a parent use to create a child process and to wait for it to finish? | Unit 1_Part 2_ Process management.pdf p.34 | 2 | yes | Unit 1_Part 2_ Process management.pdf p.32-33 |
| 7 | Which multithreading model gives every user thread its own kernel thread? | Unit 1_Part 2_ Process management.pdf p.115 | 1 | yes | Unit 1_Part 2_ Process management.pdf p.113-115 |
| 8 | What three requirements must a solution to the critical section problem satisfy? | Unit 2_Process Synchronization_Deadlock.pdf p.6 | 5 | yes | Unit 2_Process Synchronization_Deadlock.pdf p.4 |
| 9 | How do binary semaphores differ from counting semaphores? | Unit 2_Process Synchronization_Deadlock.pdf p.11,12 [2/2 pages in top 5] | 1 | yes | Unit 2_Process Synchronization_Deadlock.pdf p.11 |
| 10 | What does a cycle in a resource allocation graph tell us when every resource has a single instance? | Unit 2_Process Synchronization_Deadlock.pdf p.44 | 1 | yes | Unit 2_Process Synchronization_Deadlock.pdf p.44 |
| 11 | Which of first fit, best fit and worst fit used memory most efficiently for the 212 KB, 417 KB, 112 KB and 426 KB requests? | Unit 3_Memory management.pdf p.22 | 1 | yes | Unit 3_Memory management.pdf p.21-22 |
| 12 | What is a TLB and why is it used with page tables? | Unit 3_Memory management.pdf p.43 | 1 | yes | Unit 3_Memory management.pdf p.43 |
| 13 | How many page faults does FIFO page replacement produce for the reference string with three frames? | Unit 3_Memory management.pdf p.48 | 1 | yes | Unit 3_Memory management.pdf p.47-49 |
| 14 | What is the total seek time for FCFS disk scheduling on a 200-track disk with the head starting at 50? | Unit 4_Storage management_ Disk Schduling.pdf p.10 (duplicate on p.35) | >10 | no | Unit 4_Storage management_ Disk Schduling.pdf p.38-39 |
| 15 | What are the advantages and disadvantages of the shortest seek time first disk scheduling algorithm? | Unit 4_Storage management_ Disk Schduling.pdf p.14 (duplicate on p.39) | 1 | yes | Unit 4_Storage management_ Disk Schduling.pdf p.38-39 |
| 16 | What are the three methods of allocating disk blocks to files? | Unit 5_Part 1_File-system-interface.pdf p.45 | 1 | yes | Unit 5_Part 1_File-system-interface.pdf p.44-46 |
| 17 | How can a dangling pointer be avoided when a file shared in an acyclic-graph directory is deleted? | Unit 5_Part 1_File-system-interface.pdf p.26 | 1 | yes | Unit 5_Part 1_File-system-interface.pdf p.25-26 |
| 18 | What do the three digits of chmod 761 mean for owner, group and public? | Unit 5_Part 1_File-system-interface.pdf p.38 | 1 | yes | Unit 5_Part 1_File-system-interface.pdf p.37-38 |
| 19 | How does a UNIX process change its protection domain with the setuid bit, su and sudo? | Unit 5_Part 2_System Protection.pdf p.7 | 1 | yes | Unit 5_Part 2_System Protection.pdf p.7 |
| 20 | In an access matrix, what do the rows and columns represent? | Unit 5_Part 2_System Protection.pdf p.10 | 1 | yes | Unit 5_Part 2_System Protection.pdf p.10 |
| 24 | What does fork return in the parent process, in the child process and on failure? | Unit 1_Part 2_ Process management.pdf p.35 | 1 | yes | Unit 1_Part 2_ Process management.pdf p.35-36 |
| 30 | How can the circular wait condition be eliminated to prevent deadlock? | Unit 2_Process Synchronization_Deadlock.pdf p.36 | 2 | yes | Unit 2_Process Synchronization_Deadlock.pdf p.26-28 |
| 36 | What does the modified (dirty) bit in a page table entry indicate? | Unit 3_Memory management.pdf p.33 | 1 | yes | Unit 3_Memory management.pdf p.33 |
| 42 | How do UNIX file system semantics differ from AFS session semantics for shared files? | Unit 5_Part 1_File-system-interface.pdf p.36 | 1 | yes | Unit 5_Part 1_File-system-interface.pdf p.35-36 |
| 48 | How does starvation arise in round robin CPU scheduling and in shortest seek time first disk scheduling? | Unit 1_Part 2_ Process management.pdf p.74 + Unit 4_Storage management_ Disk Schduling.pdf p.14 (duplicate on p.39) [0/2 pages in top 5] [0/2 files in top 5] | 10 | no | Unit 4_Storage management_ Disk Schduling.pdf p.34-36 |
| 66 | What are the always-running background helpers that start at boot, such as print servers, usually called? | Unit 1_Part 1_Introduction & OS Structure.pdf p.48 | 1 | yes | Unit 1_Part 1_Introduction & OS Structure.pdf p.48 |
| 68 | Why is saving one task's registers and loading another's considered wasted time, and how long does it typically take? | Unit 1_Part 2_ Process management.pdf p.30 | 7 | no | Unit 1_Part 2_ Process management.pdf p.23-27 |
| 70 | What happens to a time-slice based policy when the slice is made extremely large? | Unit 1_Part 2_ Process management.pdf p.77 | >10 | no | Unit 1_Part 2_ Process management.pdf p.74 |
| 72 | How can five diners who share utensils be seated and ordered so that nobody waits forever? | Unit 2_Process Synchronization_Deadlock.pdf p.15 | 1 | yes | Unit 2_Process Synchronization_Deadlock.pdf p.15 |
| 74 | Once a circular hold among jobs has been detected, how can it be broken by killing jobs or taking things away from them? | Unit 2_Process Synchronization_Deadlock.pdf p.57,58,59 [1/3 pages in top 5] | 1 | yes | Unit 2_Process Synchronization_Deadlock.pdf p.57 |
| 76 | Which flag in a translation-table row says whether the requested block is resident in main memory, and what is it called when it is not? | Unit 3_Memory management.pdf p.32 | 1 | yes | Unit 3_Memory management.pdf p.31-33 |
| 78 | What determines how much data a traditional hard drive can store? | Unit 4_Storage management_ Disk Schduling.pdf p.6 (duplicate on p.31) | 2 | yes | Unit 5_Part 1_File-system-interface.pdf p.59-60 |
| 80 | In what ways can a permission that was granted earlier be taken back, and how do keys make this possible? | Unit 5_Part 2_System Protection.pdf p.24 | 1 | yes | Unit 5_Part 2_System Protection.pdf p.23-24 |

## Misses (4)

- What is the total seek time for FCFS disk scheduling on a 200-track disk with the head starting at 50? (expected Unit 4_Storage management_ Disk Schduling.pdf p.10, got Unit 4_Storage management_ Disk Schduling.pdf p.38-39)
- How does starvation arise in round robin CPU scheduling and in shortest seek time first disk scheduling? (expected Unit 1_Part 2_ Process management.pdf p.74, Unit 4_Storage management_ Disk Schduling.pdf p.14, got Unit 4_Storage management_ Disk Schduling.pdf p.34-36)
- Why is saving one task's registers and loading another's considered wasted time, and how long does it typically take? (expected Unit 1_Part 2_ Process management.pdf p.30, got Unit 1_Part 2_ Process management.pdf p.23-27)
- What happens to a time-slice based policy when the slice is made extremely large? (expected Unit 1_Part 2_ Process management.pdf p.77, got Unit 1_Part 2_ Process management.pdf p.74)
