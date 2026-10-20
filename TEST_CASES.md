# HintOS test cases

Use these cases to check the tutor in the browser. This is a human-run checklist; HintOS does not load it or use its expected results as reply templates. Install and download the Ollama model as described in README.md. Start HintOS offline, open `http://127.0.0.1:8000`, and check that the status says **Local OS tutor is ready**. Click **New question** before starting a separate case. For generated language, check meaning and relevance rather than exact wording. Exact values below are only for the deterministic Banker calculator/checker.

After an exercise, enter `did that`. Expected behavior: HintOS asks what answer or work you got and offers to check it; it does not send the same hint again. Try `I don't understand` too. HintOS should ask which step was confusing.

To check that follow-up context survives a server restart, start a question and wait for its hint, stop and restart the server, then enter `did that`. HintOS should still ask for the answer to the earlier question. This uses the latest unfinished attempt in the SQLite history.

Try questions in your own words, such as `Why does fork make another process?`, `My pages keep faulting even though the program is running`, or `How is a container different from a virtual machine?`. The reply should explain the actual issue in simple English. A greeting such as `hi` should get a natural welcome, not a random OS hint.

## Basic concept questions

Start a new question and enter `what does Need mean?`.

Expected behavior: It explains what Need means in this context and states `Need = Max - Allocation` in its own natural wording. It should be labeled `Tutor`, with no notes list.

Try `what is a page fault?`. HintOS should explain that the referenced page is not currently in physical memory and the OS must load it or report an error.

While a numeric problem is active, ask `what does Need mean?`, then submit your matrix. HintOS should answer the definition and still check the matrix against the original problem.

## Adaptive hint flow: Banker's Algorithm

1. Enter: `In Banker's Algorithm, is Need = Max + Allocation?`

   Expected reply: It should explain what Need represents or ask a relevant guiding question. It should not return an unrelated generic OS hint.

2. For the same question, enter: `I think we add because Allocation is the resources needed.`

   Expected reply: It should respond to the student's stated reason and explain the difference between Max and Allocation.

3. For the same question, enter: `Need = Max - Allocation`

   Expected behavior: It recognizes the formula as correct, addresses it directly, and offers a relevant next step. Wording and adaptive label may vary with the conversation stage.

The UI should label exercise replies with an adaptive stage such as `Recall`, `Identify`, `Diagnose`, `Direct`, or `Scaffold`. Basic definition replies can use `Concept`. It should not show a `Notes:` line or source filenames.

### Complete-response regression: CPU scheduling

Start a new conversation and ask: `Find waiting times for P1 (arrival 0, burst 5) and P2 (arrival 1, burst 3) using Round Robin with quantum 2.`

Expected first reply: one short, complete hint that asks the student to build the first time slice or track the ready queue. It must not dump the finished schedule, invent negative waiting times, expose self-correction text (for example, “wait, let me recalculate”), or end mid-sentence. If the local model reaches its output limit, HintOS retries once and never displays the partial draft.

## Check a numerical Need matrix

Click **New question**, then enter this problem using the shown matrix format:

`Calculate Need. Max=[[7,5,3],[3,2,2]] Allocation=[[0,1,0],[2,0,0]]`

Expected first hint: It guides the student to subtract Allocation from Max without immediately filling in the whole matrix, and invites them to share their attempt. Wording should vary naturally.

Enter `done` before sending an answer. Expected check-in: HintOS asks you to send your result or steps. It should not repeat the same hint.

Now enter the incorrect matrix `[[7,4,3],[1,1,2]]`.

Expected feedback: It identifies the incorrect cell (P1, second resource), explains the subtraction to recheck, and invites a correction. The label should be `Diagnose`; prose should be generated naturally.

Now enter `[[7,4,3],[1,2,2]]`.

Expected feedback: HintOS says `Correct` and confirms that every cell matches Max minus Allocation. The conversation ends for that problem.

To check progressive help, start the same matrix problem again and submit five incorrect matrices, one at a time. HintOS should progress through Recall, Identify, Diagnose, Direct, and Scaffold while pointing out what to reconsider. After the fifth unsuccessful submission, it should show the correct matrix and explain the subtraction. If you submit the correct matrix at any stage, it should confirm it instead of revealing a solution.

## Check a safe sequence with numbers

Click **New question**, then enter:

`Find a safe sequence. Available=[3,3,2] Max=[[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]] Allocation=[[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]]`

HintOS should ask you to compare each process's Need with Available and enter a process order. Submit `P1, P3, P4, P0, P2`.

Expected feedback: HintOS says `Correct` and confirms that each process can run with the resources available at that step. Other safe orders are accepted too.

Start the same question again and submit `P0, P1, P2, P3, P4`.

Expected feedback: `Not quite. P0 cannot run at that point with the currently available resources. Check its Need against Available before choosing it.`

## Natural tutoring conversation

1. Ask `What is a context switch?` HintOS should define it directly in plain English.
2. Follow with `` HintOS should understand that “that” means a context switch and continue the explanation.
3. Say `Give me a small example.` The reply should give a relevant OS example, not restart the topic.
4. Ask `What is the difference between a process and a thread?` HintOS should compare them clearly.
5. Ask an unrelated question such as `How do I bake a cake?` HintOS should politely redirect to OS topics.
6. Ask a numerical CPU scheduling problem with arrival and burst times. HintOS should explain a calculation approach, and respond to follow-up questions using the same problem context.

### Problem-solving should teach before solving

1. Ask: `For Round Robin with quantum 2, P1 arrives at 0 with burst 5 and P2 arrives at 1 with burst 2. Find the waiting times.` The first reply should give one small setup hint (for example, how to begin the timeline) and ask you to try that step. It must not provide the completed schedule or waiting times.
2. Submit a proposed first step or answer. HintOS should assess that work, identify the first mistake if there is one, and give a focused next hint rather than restarting or solving everything.
3. Ask a related concept question such as `What does quantum mean here?` HintOS should explain the concept directly, then leave the original exercise available to continue.
4. HintOS should progress through Recall, Identify, Diagnose, Direct, and Scaffold as unsuccessful work continues. After five unsuccessful work attempts, it should provide a worked solution with the key steps. A correct attempt should be confirmed at any stage instead of being treated as failure.
5. Ask `Show me the full solution` at any stage. HintOS should honor this explicit request.

### Context must follow the latest concept

1. Ask `What is a process control block?` HintOS should explain the PCB.
2. Ask `what does state mean here?`

Expected: HintOS explains **process state** (such as ready, running, or blocked) and connects it to the PCB. It must not show a Banker’s Algorithm hint, even if an older Banker exercise was discussed before this question.

### Follow-up versus a new question

1. Enter `Banker's Algorithm`, then reply `process with lowest need first`.

   Expected: HintOS corrects the rule directly: a process is eligible only when every Need value is no greater than the matching Available value. It must not answer with a generic first hint.

2. Without clicking **New question**, enter `What is a page fault?`.

   Expected: HintOS answers the page-fault question directly instead of treating it as an answer to the Banker question.

3. Ask `What is a context switch?`, then `Why does the OS need to do that?`.

   Expected: The second reply explains why an OS performs a context switch and keeps the context-switch topic; it does not start an unrelated topic.

4. Ask a concept question, then use **New question** and ask `What is a thread?`.

   Expected: The old exercise is cleared and the thread question is answered on its own.

5. Ask `What is a page fault?`, then ask `In Banker's Algorithm, is Need = Max + Allocation?`

   Expected: HintOS switches to Banker’s Algorithm despite the sentence starting with “In”, and directly explains that `Need = Max - Allocation`. It must not return a page-replacement hint.

6. While any other topic is active, ask `What is a context switch?`

   Expected: HintOS defines a context switch and mentions saving/restoring CPU state. It must not ask the generic “what part are you unsure about?” question.

### Reference, clarification, and hypothetical questions across OS topics

Run each sequence as one conversation. Start the next sequence with **New question**.

1. **Past reference:** Ask `What is a context switch?`, then `What did you say the OS saves?` and `Why does it save that?`
   Expected: Both replies refer to the context-switch explanation and describe saved process state, such as the program counter and registers.
2. **Current reference:** Ask `Explain paging in simple terms`, then `What does the page table do here?`
   Expected: “Here” means paging; the reply connects the page table to mapping virtual pages to physical frames.
3. **Hypothetical follow-up:** Ask `What happens during a page fault?`, then `What if the page is already in memory?`
   Expected: It explains that a valid resident page should not require disk loading, and distinguishes a TLB miss from a page fault if relevant.
4. **Switch to another topic:** Ask `What is a semaphore?`, then `Can you explain inode allocation?`
   Expected: The second reply answers about file systems and does not continue the semaphore explanation.
5. **Same-topic clarification:** Ask `How does Round Robin work?`, then `What if the time quantum is too small?`
   Expected: It explains the context-switch overhead tradeoff and keeps the scheduling context.
6. **Student correction:** Ask about deadlock prevention, then say `I meant avoidance, not prevention`.
   Expected: HintOS accepts the correction and explains avoidance, rather than repeating prevention.
7. **Ambiguous reference:** Ask a question involving both a process and a thread, then ask `Does it share memory?`
   Expected: If the referent is genuinely unclear, HintOS asks whether “it” means the process or thread instead of guessing.
8. **Restart restore:** Ask a multi-turn OS question, restart the server, and reload the page.
   Expected: The active transcript is restored and the next follow-up uses the same topic.
9. **No stale repeated question:** Ask the exact same question, click **New question**, and ask it again.
   Expected: The new conversation does not include hints or responses from the earlier attempt.

### Syllabus coverage smoke check

Ask one question from each area below. Each response should answer the actual question in simple English, stay within Operating Systems, and use a useful example or one focused next step when appropriate:

- OS purpose, structure models, abstractions, resources, security, networking, and multimedia.
- System calls, APIs, protection, user/kernel modes, interrupts, PCBs, Unix process management, and threads.
- Preemptive and non-preemptive scheduling, scheduling algorithms, and performance measures.
- Synchronization, critical sections, semaphores, monitors, classic concurrency problems, and IPC.
- Deadlock conditions, graphs, prevention, avoidance, detection, recovery, and Banker’s Algorithm.
- Memory allocation, fragmentation, paging, segmentation, virtual memory, page tables, TLBs, page faults, and replacement.
- File interfaces, implementation, recovery, journaling, soft updates, log-structured and distributed file systems.
- Disk structure, attachment, scheduling, threats, malware, security policy versus mechanism, authentication, access matrices, capabilities, performance, scaling, and mobile OS.

If a question is underspecified, HintOS should ask for the missing detail instead of inventing values. If the question asks for a complete worked solution, it may show the full steps; otherwise it should teach one useful step at a time.

### Banker input validation

In `/docs`, submit a Banker request with mismatched resource-column counts, a negative resource value, or an `Available` vector with the wrong length. Each invalid request should return HTTP 422 with a readable explanation, not a server error or a guessed safe sequence.

## Banker's Algorithm calculator

Open `http://127.0.0.1:8000/docs`, expand `POST /bankers`, choose **Try it out**, paste the JSON below, and execute it:

```json
{
  "available": [3, 3, 2],
  "maximum": [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]],
  "allocation": [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
}
```

Expected response:

```json
{
  "need": [[7, 4, 3], [1, 2, 2], [6, 0, 0], [0, 1, 1], [4, 3, 1]],
  "safe": ["P1", "P3", "P4", "P0", "P2"]
}
```

Then change `available` to `[0, 0, 0]`. The expected `safe` value is `null`, because no process can start with those available resources.

## Offline check

Download Ollama's model and BGE before disconnecting from the internet. Then disconnect, keep Ollama running, and start HintOS with `HINTOS_OFFLINE=1`. Ask a new concept question and continue it with a follow-up. The status should say the local tutor is ready, and the answer should still arrive. The exact sentences may differ between runs.
