// Real output, recorded from the live demo on 2026-11-03 (originals in docs/ui/captured/). The landing page shows these
// instead of calling the model, so it costs no AI quota and keeps working if the quota runs out.
export type RecordedSource = { n: number; label: string; section: string | null; text: string; cited: boolean; image_url: string };

export const RECORDED_ANSWER: { question: string; mode: string; text: string; sources: RecordedSource[] } = {
  "question": "Explain the SCAN disk scheduling algorithm with its advantages and disadvantages.",
  "mode": "concise",
  "text": "The SCAN algorithm moves the disk head in one direction, serving all pending requests until it reaches the end of the disk, then reverses direction and continues serving requests [5]. It is easy to implement [1]. Requests do not have to wait in a queue [1]. The head continues to the end of the disk even when there are no requests in that direction [1].",
  "sources": [
    {
      "n": 1,
      "label": "Unit 4_Storage management_ Disk Schduling, p.17",
      "section": "SCAN Disk Scheduling Algorithm",
      "text": "SCAN Disk Scheduling Algorithm\nAdvantages:\nâ€¢ Implementation is easy.\nâ€¢ Requests do not have to wait in a queue.\nDisadvantage:\nâ€¢ The head keeps going on to the end even if there are\nno requests in that direction.",
      "cited": true,
      "image_url": "/demo/pages/5/17.webp"
    },
    {
      "n": 2,
      "label": "Unit 4_Storage management_ Disk Schduling, p.20",
      "section": "C-SCAN Disk Scheduling Algorithm",
      "text": "C-SCAN Disk Scheduling Algorithm\nAdvantages:\nâ€¢ The waiting time is uniformly distributed among the requests.\nâ€¢ Response time is good in it.\nDisadvantages:\nâ€¢ The time taken by the disk arm to locate a spot is increased here.\nâ€¢ The head keeps going to the end of the disk.",
      "cited": false,
      "image_url": "/demo/pages/5/20.webp"
    },
    {
      "n": 3,
      "label": "Unit 4_Storage management_ Disk Schduling, p.23",
      "section": "LOOK Disk Scheduling Algorithm",
      "text": "LOOK Disk Scheduling Algorithm\nAdvantages:\nâ€¢ Starvation does not occur.\nâ€¢ Since the head does not go to the end of the disk, the time is not\nwasted here.\nDisadvantage:\nâ€¢ The arm has to be conscious to find the last request",
      "cited": false,
      "image_url": "/demo/pages/5/23.webp"
    },
    {
      "n": 4,
      "label": "Unit 4_Storage management_ Disk Schduling, p.26",
      "section": "C-LOOK Disk Scheduling Algorithm",
      "text": "C-LOOK Disk Scheduling Algorithm\nAdvantages:\nâ€¢ The waiting time is decreased.\nâ€¢ If there are no requests till the end, it reverses the head direction immediately.\nâ€¢ Starvation does not occur.\nâ€¢ The time taken by the disk arm to find the desired spot is less.\nDisadvantage:\nâ€¢ The arm has to be conscious about finding the last request.",
      "cited": false,
      "image_url": "/demo/pages/5/26.webp"
    },
    {
      "n": 5,
      "label": "Unit 4_Storage management_ Disk Schduling, p.15",
      "section": "SCAN Disk Scheduling Algorithm",
      "text": "SCAN Disk Scheduling Algorithm\nIn this algorithm, the head starts to scan all the requests in a direction and\nreaches the end of the disk. After that, it reverses its direction and starts to\nscan again the requests in its path and serves them. Due to this feature, this\nalgorithm is also known as the \"Elevator Algorithm\".",
      "cited": true,
      "image_url": "/demo/pages/5/15.webp"
    }
  ]
};

export const RECORDED_REFUSAL = {"question": "How does TCP congestion control work?", "text": "Not in your notes."};

export const RECORDED_QUIZ = {
  "question": "What does the term 'Rotational Latency' refer to according to the slides?",
  "options": [
    "The time taken by the disk arm to locate the desired track",
    "The time taken for a sector to rotate under the read/write head",
    "The time taken to transfer data from disk to CPU",
    "The sum of seek time, rotational latency, and transfer time"
  ],
  "answer": 1,
  "explanation": "Rotational Latency is defined as the time taken by a desired sector of the disk to rotate to the position where it can be accessed by the read/write heads.",
  "label": "Unit 4_Storage management_ Disk Schduling, p.4"
};
