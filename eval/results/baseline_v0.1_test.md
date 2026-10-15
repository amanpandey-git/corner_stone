# Retrieval evaluation - split `test` - v0.1 baseline (Stage 1 code, unchanged)

Generated 2026-10-15 by `eval/retrieval_eval.py --split test`. Index: 7 documents, 328 vectors, model `BAAI/bge-small-en-v1.5`, ef_search=50. Nothing was tuned on the test split.

## Summary

| metric | value |
|---|---|
| scored questions | 25 |
| **hit@5** | **0.960** (24/25) |
| **MRR** (top-10) | **0.912** |
| multi-page questions | 8: 15/17 labelled pages found in top 5 |
| cross-file questions | 4: 2 with every file in top 5 |
| end-to-end search latency p50 / p95 | 43 ms / 110 ms (query embedding + HNSW + SQLite, k=10) |
| unanswerable questions in split | 10 (not scored here; Phase 2 abstention) |

Definitions: a result covers a labelled page if it is from that target's file and the page lies inside the chunk's page range. hit@5 = any labelled page covered in the top 5. MRR = mean of 1/rank of the first covering result (top 10, else 0).

## Excluded from scoring

The three questions asked by hand in Step 5 (their results were shown to the author before evaluation):

- What are the four necessary conditions for deadlock?
- What is the difference between a process and a thread?
- How does paging avoid external fragmentation?

## Per question

| id | question | expected | rank | hit@5 | top result |
|---|---|---|---|---|---|
| 21 | What are the four components of a computer system? | Unit 1_Part 1_Introduction & OS Structure.pdf p.11 | 1 | yes | Unit 1_Part 1_Introduction & OS Structure.pdf p.11 |
| 22 | Besides user services, which three services does the OS provide to keep the system itself running efficiently? | Unit 1_Part 1_Introduction & OS Structure.pdf p.16 | 1 | yes | Unit 1_Part 1_Introduction & OS Structure.pdf p.16-17 |
| 23 | What is a real-time operating system, what types exist and what are its advantages? | Unit 1_Part 1_Introduction & OS Structure.pdf p.37,38 [2/2 pages in top 5] | 1 | yes | Unit 1_Part 1_Introduction & OS Structure.pdf p.35-37 |
| 25 | Using exponential averaging with alpha 0.5, what is the predicted burst time for the fifth process? | Unit 1_Part 2_ Process management.pdf p.63 | 1 | yes | Unit 1_Part 2_ Process management.pdf p.61-63 |
| 26 | What is the convoy effect in FCFS CPU scheduling? | Unit 1_Part 2_ Process management.pdf p.48 | 1 | yes | Unit 1_Part 2_ Process management.pdf p.47-50 |
| 27 | What are the five basic states a process goes through from creation to termination? | Unit 1_Part 2_ Process management.pdf p.9,10 [2/2 pages in top 5] | 1 | yes | Unit 1_Part 2_ Process management.pdf p.8-9 |
| 28 | What happens to the whole process when a user-level thread performs a blocking operation, compared with a kernel-level thread? | Unit 1_Part 2_ Process management.pdf p.108 | 1 | yes | Unit 1_Part 2_ Process management.pdf p.107-108 |
| 29 | What is the minimum number of units of a resource that guarantees no deadlock for n processes? | Unit 2_Process Synchronization_Deadlock.pdf p.30 | 1 | yes | Unit 2_Process Synchronization_Deadlock.pdf p.30-31 |
| 31 | Which data structures (Available, Max, Allocation, Need) does the Banker's algorithm maintain and what do they mean? | Unit 2_Process Synchronization_Deadlock.pdf p.48 | 1 | yes | Unit 2_Process Synchronization_Deadlock.pdf p.47-48 |
| 32 | What is the difference between a safe state and an unsafe state? | Unit 2_Process Synchronization_Deadlock.pdf p.38 | 1 | yes | Unit 2_Process Synchronization_Deadlock.pdf p.38 |
| 33 | In the first and second readers-writers problems, who can starve? | Unit 2_Process Synchronization_Deadlock.pdf p.17 | 1 | yes | Unit 2_Process Synchronization_Deadlock.pdf p.16-17 |
| 34 | What are the advantages and disadvantages of dynamic partitioning? | Unit 3_Memory management.pdf p.16 | 1 | yes | Unit 3_Memory management.pdf p.16 |
| 35 | For a logical address space of eight pages of 1024 words mapped onto 32 frames, how many bits are in the logical and physical addresses? | Unit 3_Memory management.pdf p.41,42 [2/2 pages in top 5] | 1 | yes | Unit 3_Memory management.pdf p.42 |
| 37 | How many page faults does LRU page replacement give for the reference string with three frames? | Unit 3_Memory management.pdf p.49 | 1 | yes | Unit 3_Memory management.pdf p.47-49 |
| 38 | Why is the SCAN disk scheduling algorithm called the elevator algorithm? | Unit 4_Storage management_ Disk Schduling.pdf p.15 (duplicate on p.40) | 1 | yes | Unit 4_Storage management_ Disk Schduling.pdf p.40-42 |
| 39 | What is the total seek time for C-LOOK on the request sequence 82, 170, 43, 140, 24, 16, 190 with the head at 50? | Unit 4_Storage management_ Disk Schduling.pdf p.25 (duplicate on p.50) | 3 | yes | Unit 4_Storage management_ Disk Schduling.pdf p.43-45 |
| 40 | What is the difference between mandatory and advisory file locking? | Unit 5_Part 1_File-system-interface.pdf p.9 | 1 | yes | Unit 5_Part 1_File-system-interface.pdf p.9 |
| 41 | What are the advantages and drawbacks of contiguous allocation of disk blocks? | Unit 5_Part 1_File-system-interface.pdf p.46 | 7 | no | Unit 3_Memory management.pdf p.8-9 |
| 43 | What is the principle of least privilege? | Unit 5_Part 2_System Protection.pdf p.5 | 1 | yes | Unit 5_Part 2_System Protection.pdf p.5 |
| 44 | How do access lists for objects differ from capability lists for domains when implementing the access matrix? | Unit 5_Part 2_System Protection.pdf p.18,19,20 [3/3 pages in top 5] | 1 | yes | Unit 5_Part 2_System Protection.pdf p.20 |
| 45 | How does Java protect privileged operations using protection domains and stack inspection? | Unit 5_Part 2_System Protection.pdf p.27 | 1 | yes | Unit 5_Part 2_System Protection.pdf p.27 |
| 46 | What is a race condition and how can it be avoided? | Unit 1_Part 1_Introduction & OS Structure.pdf p.17 + Unit 2_Process Synchronization_Deadlock.pdf p.5 [1/2 pages in top 5] [1/2 files in top 5] | 1 | yes | Unit 2_Process Synchronization_Deadlock.pdf p.4-5 |
| 47 | What is a semaphore and how is it used for synchronization between processes? | Unit 1_Part 2_ Process management.pdf p.15 + Unit 2_Process Synchronization_Deadlock.pdf p.10 [2/2 pages in top 5] [2/2 files in top 5] | 1 | yes | Unit 1_Part 2_ Process management.pdf p.15 |
| 49 | What is protection in an operating system and how does an access matrix represent it? | Unit 1_Part 1_Introduction & OS Structure.pdf p.24 + Unit 5_Part 2_System Protection.pdf p.10 [2/2 pages in top 5] [2/2 files in top 5] | 1 | yes | Unit 1_Part 1_Introduction & OS Structure.pdf p.24 |
| 50 | What memory-management activities is the OS responsible for, and how does paging turn a logical address into a physical address? | Unit 1_Part 1_Introduction & OS Structure.pdf p.19 + Unit 3_Memory management.pdf p.27 [1/2 pages in top 5] [1/2 files in top 5] | 3 | yes | Unit 3_Memory management.pdf p.24-25 |

## Misses (1)

- What are the advantages and drawbacks of contiguous allocation of disk blocks? (expected Unit 5_Part 1_File-system-interface.pdf p.46, got Unit 3_Memory management.pdf p.8-9)
