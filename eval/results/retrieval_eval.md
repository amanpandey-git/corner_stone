# Retrieval evaluation (labelled questions)

Generated 2026-10-15 by `eval/retrieval_eval.py`. Index: 7 documents, 328 vectors, model `BAAI/bge-small-en-v1.5`, ef_search=50. Nothing was tuned on these questions.

## Summary

| metric | value |
|---|---|
| scored questions | 20 |
| **hit@5** | **0.950** (19/20) |
| **MRR** (top-10) | **0.885** |
| multi-page questions | 3: 5/6 labelled pages found in top 5 |
| end-to-end search latency p50 / p95 | 35 ms / 57 ms (query embedding + HNSW + SQLite, k=10) |

Definitions: a result covers a labelled page if it is from the labelled file and the page lies inside the chunk's page range. hit@5 = any labelled page covered in the top 5. MRR = mean of 1/rank of the first covering result (top 10, else 0).

## Excluded from scoring

The three questions asked by hand in Step 5 (their results were shown to the author before evaluation):

- What are the four necessary conditions for deadlock?
- What is the difference between a process and a thread?
- How does paging avoid external fragmentation?

## Per question

| # | question | expected | rank | hit@5 | top result |
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

## Misses (1)

- What is the total seek time for FCFS disk scheduling on a 200-track disk with the head starting at 50? (expected Unit 4_Storage management_ Disk Schduling.pdf p.[10], got Unit 4_Storage management_ Disk Schduling.pdf p.38-39)
