import ast
import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from llm.client import is_definition_question, make_tutor_reply
from problems.bankers import calculate_need, safe_sequence
from rag.retriever import Retriever

HINT_TYPES = ["Recall", "Identify", "Diagnose", "Direct", "Scaffold"]
SOLUTION_AFTER_ATTEMPTS = len(HINT_TYPES)


class Tutor:
    def __init__(self, base_dir):
        self.db_path = Path(base_dir) / "hintos.db"
        self.retriever = Retriever(Path(base_dir) / "knowledge")
        self.last_problem = ""
        self.last_gap = ""
        self.numeric_task = None
        self.active_since_id = 0
        self._create_table()
        self._load_state()

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.db_path)
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _create_table(self):
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem TEXT, response TEXT, hint_type TEXT, hint TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS tutor_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_problem TEXT, last_gap TEXT, numeric_task TEXT,
                active_since_id INTEGER NOT NULL DEFAULT 0
            )""")
            columns = {row[1] for row in db.execute("PRAGMA table_info(tutor_state)")}
            if "active_since_id" not in columns:
                db.execute("ALTER TABLE tutor_state ADD COLUMN active_since_id INTEGER NOT NULL DEFAULT 0")

    def _load_state(self):
        with self._connect() as db:
            row = db.execute(
                "SELECT last_problem, last_gap, numeric_task, active_since_id FROM tutor_state WHERE id = 1"
            ).fetchone()
            latest_attempt = None
            if not row:
                latest_attempt = db.execute(
                    "SELECT problem, hint_type FROM attempts ORDER BY id DESC LIMIT 1"
                ).fetchone()
        if row:
            self.last_problem, self.last_gap = row[0] or "", row[1] or ""
            self.numeric_task = json.loads(row[2]) if row[2] else None
            self.active_since_id = row[3] or 0
            if self.last_problem and self.active_since_id == 0:
                with self._connect() as db:
                    start = db.execute(
                        "SELECT MIN(id) FROM attempts WHERE problem = ?", (self.last_problem,)
                    ).fetchone()[0]
                self.active_since_id = max((start or 1) - 1, 0)
                self._save_state()
        elif latest_attempt and latest_attempt[1] != "Correct":
            self.last_problem = latest_attempt[0] or ""
            self.last_gap = self._find_gap(self.last_problem)
            self.numeric_task = self._read_banker_need_problem(self.last_problem)
            with self._connect() as db:
                start = db.execute(
                    "SELECT MIN(id) FROM attempts WHERE problem = ?", (self.last_problem,)
                ).fetchone()[0]
            self.active_since_id = max((start or 1) - 1, 0)
            self._save_state()

    def _save_state(self):
        with self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO tutor_state (id, last_problem, last_gap, numeric_task, active_since_id) VALUES (1, ?, ?, ?, ?)",
                (self.last_problem, self.last_gap, json.dumps(self.numeric_task) if self.numeric_task else None,
                 self.active_since_id),
            )

    def _begin_conversation(self):
        with self._connect() as db:
            self.active_since_id = db.execute("SELECT COALESCE(MAX(id), 0) FROM attempts").fetchone()[0]

    def _recent(self, problem):
        with self._connect() as db:
            rows = db.execute(
                "SELECT response, hint FROM attempts WHERE problem = ? AND id > ? ORDER BY id DESC LIMIT 12",
                (problem, self.active_since_id),
            ).fetchall()
        return list(reversed(rows))

    def reply(self, message):
        message = message.strip()
        if not message:
            return {"message": "Type a question or try an answer first.", "response_type": "help"}

        reset_prefix = re.match(
            r"^(?:new question|start a new question|start over|new topic)\s*[:,\-]?\s*(.*)$",
            message, re.I | re.S,
        )
        if reset_prefix:
            self.reset()
            message = reset_prefix.group(1).strip()
            if not message:
                return {"message": "Ready for a new OS question. What would you like to work on?", "response_type": "help"}

        # Simple greetings should not wait for embeddings or the local chat model.
        greeting = re.sub(r"[^a-z ]", " ", message.lower())
        greeting = re.sub(r"\s+", " ", greeting).strip()
        if greeting in {"hi", "hello", "hey", "hi there", "hello there", "hey there", "good morning", "good afternoon", "good evening"}:
            return {
                "message": "Hi! What Operating Systems topic or problem would you like help with?",
                "response_type": "chat",
                "hint_type": "",
                "sources": [],
            }

        # Remember a bare topic as the conversation anchor, then let the model
        # respond naturally and handle whatever the student says next.
        topic_prompt = re.sub(r"[^a-z0-9 ]", " ", message.lower())
        topic_prompt = re.sub(r"\s+", " ", topic_prompt).strip()
        quick_topics = {
            "banker": "Banker's Algorithm", "bankers": "Banker's Algorithm",
            "bankers algorithm": "Banker's Algorithm", "deadlock": "deadlocks",
            "cpu scheduling": "CPU scheduling", "paging": "memory management",
            "process": "processes and threads", "processes": "processes and threads",
            "threads": "processes and threads", "memory management": "memory management",
            "semaphores": "process synchronization", "file systems": "file systems",
        }
        if topic_prompt in quick_topics:
            # Keep a usable conversation anchor: the next message may be a
            # follow-up answer to this topic prompt (for example, a Banker
            # misconception). Leaving it empty made that reply look like a
            # brand-new question.
            self._begin_conversation()
            self.last_problem = ""
            self.last_gap = quick_topics[topic_prompt]
            self.numeric_task = None
            self._save_state()

        # Mark concept questions for UI labeling; let the local model answer
        # using the full conversation instead of a canned definition.
        definition_question = is_definition_question(message)

        # A short follow-up uses the last problem as its context.
        follow_up = bool(self.last_problem)
        if follow_up and self._should_switch_context(message):
            self.last_problem = ""
            self.last_gap = ""
            self.numeric_task = None
            follow_up = False
        if follow_up:
            problem = self.last_problem
            response = message
        else:
            problem = message
            response = ""
            self._begin_conversation()
            self.last_problem = problem
            self.numeric_task = self._read_banker_need_problem(problem)
            self._save_state()

        if response and not self.numeric_task:
            combined_problem = problem + "\n" + response
            task_from_follow_up = self._read_banker_need_problem(combined_problem)
            if task_from_follow_up:
                self.numeric_task = task_from_follow_up
                problem = combined_problem
                self.last_problem = combined_problem
                response_has_answer = (
                    bool(re.search(r"need\s*[:=]\s*\[\[", message, re.I))
                    if task_from_follow_up["type"] == "banker_need"
                    else bool(re.search(r"\bP\s*\d+\b", message, re.I))
                )
                if not response_has_answer:
                    response = ""
                self._save_state()

        if response and self.numeric_task and self._is_acknowledgement(response):
            if self.numeric_task and self.numeric_task["type"] == "banker_safe":
                ask = "Great. What process order did you get? Send the process IDs in order, such as P1, P3, P4, P0, P2, and I'll check each step."
            elif self.numeric_task and self.numeric_task["type"] == "banker_need":
                ask = "Great. Send the Need matrix you worked out, such as [[1, 2], [3, 4]], and I'll check each value."
            elif "banker" in self.last_gap.lower() or "deadlock" in self.last_gap.lower():
                ask = "Great. Send the process order or result you got, and I'll check it. If the question has resource numbers, include the Available, Max, and Allocation values too."
            else:
                ask = "Great. Send the answer or steps you worked out, and I'll check them with you."
            return {
                "message": ask,
                "response_type": "check_in",
                "hint_type": "",
                "sources": [],
            }

        # A follow-up often contains pronouns and fragments. Classifying the
        # concatenated old problem plus short reply can shift topics by
        # accident, so retain the established topic for conversational turns.
        if follow_up:
            gap = self.last_gap or self._find_gap(problem)
        else:
            gap = self._find_gap(problem)
            if gap:
                self.last_gap = gap
        gap = gap or self.last_gap or "understanding the OS idea"
        self._save_state()

        if response and gap == "Banker's Algorithm" and not self.numeric_task:
            process_ids = re.findall(r"\bP\s*\d+\b", response, re.I)
            if process_ids:
                message = (
                    "I can check that process order, but I need the numbers too. Send Available, Max, and Allocation, "
                    "then I can check each step of the sequence."
                )
                return {
                    "message": message, "response_type": "check_in", "topic": gap,
                    "hint_type": "Identify", "sources": [],
                }

        if response and self.numeric_task:
            if self.numeric_task["type"] == "banker_need":
                checked = self._check_banker_need_answer(problem, response, gap)
            else:
                checked = self._check_banker_safe_answer(problem, response, gap)
            if checked:
                return checked

        if response and gap == "Banker's Algorithm Need calculation" and not self.numeric_task:
            formula = response.lower().replace(" ", "").replace("minus", "-")
            if "need" in formula and "max-allocation" in formula:
                feedback = "Correct. Need is the resources still required, so calculate it as Max - Allocation. You can now use each Need row to check which process can run."
                self._save_attempt(problem, response, "Correct", feedback)
                self.last_problem = ""
                self.last_gap = ""
                self._save_state()
                return {
                    "message": feedback,
                    "response_type": "feedback",
                    "topic": gap,
                    "hint_type": "Correct",
                    "level": 0,
                    "sources": [],
                    "status": "correct",
                }

        past = self._recent(problem)
        problem_solving = bool(
            self.numeric_task or self._looks_like_problem_solving(problem)
        )
        attempts = self._learning_attempt_count(problem, response)
        level = min(attempts, len(HINT_TYPES) - 1)
        hint_type = HINT_TYPES[level]
        reveal_solution = problem_solving and (
            attempts >= SOLUTION_AFTER_ATTEMPTS or self._requests_full_solution(problem + " " + response)
        )
        notes = self.retriever.search(problem + " " + response)
        hint = make_tutor_reply(
            problem, response, gap, hint_type, notes, past,
            problem_solving=problem_solving, attempts=attempts,
            reveal_solution=reveal_solution,
        )
        reply_type = "Concept" if definition_question else "Direct" if reveal_solution else hint_type

        self._save_attempt(problem, response, reply_type, hint)

        return {
            "message": hint,
            "response_type": "chat",
            "topic": gap,
            "hint_type": reply_type,
            "level": level + 1,
            "sources": [item["source"] for item in notes],
        }

    def reset(self):
        self._begin_conversation()
        self.last_problem = ""
        self.last_gap = ""
        self.numeric_task = None
        self._save_state()
        return {"message": "Ready for a new OS question."}

    def _save_attempt(self, problem, response, hint_type, hint):
        with self._connect() as db:
            db.execute(
                "INSERT INTO attempts (problem, response, hint_type, hint) VALUES (?, ?, ?, ?)",
                (problem, response, hint_type, hint),
            )

    @staticmethod
    def _is_acknowledgement(text):
        cleaned = re.sub(r"[^a-z ]", " ", text.lower()).strip()
        return cleaned in {
            "done", "i did it", "i am done", "im done", "okay done", "ok done",
            "done i did it", "finished", "i finished", "got it", "okay", "ok",
            "did that", "i did that", "i have done that", "ive done that",
            "i already did that", "i tried that", "i tried it", "that is done",
            "yes i did that", "yeah i did that", "yeah did that", "okay i did that",
            "i have done it", "ive done it", "done that", "yeah done", "yes done",
        }

    @staticmethod
    def _is_learning_attempt(text):
        """Count submitted work or explicit struggle, but not questions/acknowledgements."""
        cleaned = re.sub(r"\s+", " ", text.lower()).strip()
        if not cleaned or Tutor._is_acknowledgement(cleaned) or Tutor._requests_full_solution(cleaned):
            return False
        if re.search(
            r"\b(?:don't|dont|do not)\s+(?:give|tell|show|reveal|solve)\b.{0,35}\b(?:answer|solution|it)\b",
            cleaned,
        ):
            return False
        if re.match(
            r"^(?:what|why|when|where|who|which|how|can you|could you|would you|"
            r"do you|is this|are these|does this|explain|define|tell me|give me a hint)\b",
            cleaned,
        ):
            return False
        return True

    @staticmethod
    def _requests_full_solution(text):
        if re.search(r"\b(?:don't|dont|do not|not)\b.{0,30}\b(answer|solution|steps)\b", text, re.I):
            return False
        return bool(re.search(
            r"\b(full|complete|worked|step[- ]by[- ]step|show (?:me )?(?:all )?(?:the )?steps|work it out|"
            r"give me (?:the )?(?:full )?(?:answer|solution)|just (?:give|tell) me the answer|"
            r"solve it for me|show the answer|reveal the answer)\b",
            text,
            re.I,
        ))

    def _learning_attempt_count(self, problem, current_response=""):
        count = 0
        for student_text, tutor_text in self._recent(problem):
            if self._is_learning_attempt(student_text):
                count += 1
            confirmation = re.sub(r"^[^a-z]+", "", tutor_text.strip().lower())
            if re.match(
                r"^(?:correct\b|exactly\b|that's right\b|that's correct\b|"
                r"that is correct\b|your answer is correct\b|yes[,! ]+(?:that's|that is) correct\b)",
                confirmation,
            ):
                count = 0
        return count + int(self._is_learning_attempt(current_response))

    @staticmethod
    def _looks_like_problem_solving(text):
        """Recognize a task to calculate, trace, choose, or construct a result."""
        if re.search(
            r"\b(calculate|compute|solve|work out|find|determine|trace|construct|schedule|draw|count|"
            r"simulate|derive|step through|perform|choose the next|select the next|"
            r"apply (?:the )?(?:fifo|lru|optimal|banker|scan|sstf)|use (?:fifo|lru|optimal|sstf|scan)|"
            r"show me (?:the )?(?:steps|work|solution))\b",
            text,
            re.I,
        ):
            return True
        lower = text.lower()
        if re.search(r"\bp\s*\d+\b", lower) and re.search(
            r"\b(arrival|burst|waiting|turnaround|completion)\b", lower
        ):
            return True
        if re.search(r"\b(how many|number of)\b", lower) and re.search(
            r"\b(page faults?|frames|head movements?|seek time)\b", lower
        ):
            return True
        if re.search(r"\b(reference string|requests?)\b", lower) and re.search(
            r"\b(frames?|tracks?|cylinder|head position)\b", lower
        ) and re.search(r"\d", lower):
            return True
        return False

    @staticmethod
    def _is_standalone_question(text):
        """Recognize common natural-language forms of independent questions."""
        lower = text.lower().strip()
        if not lower or re.search(
            r"\b(it|that|this|they|them|there|here|same|above|previous|your example)\b",
            lower,
        ):
            return False
        return bool(re.match(
            r"^(?:what\s+(?:is|are|does|do|about)|why\s+(?:is|are|does|do|should)|"
            r"how\s+(?:is|are|does|do|would)|explain\b|define\b|compare\b|differentiate\b|"
            r"tell\s+me\s+(?:about|how)\b|can\s+you\s+(?:explain|describe|teach\s+me|tell\s+me)\b|"
            r"could\s+you\s+(?:explain|describe|teach\s+me|tell\s+me)\b|"
            r"can\s+we\s+discuss\b|show\s+me\b|describe\b|summari[sz]e\b|walk\s+me\s+through\b|teach\s+me\b|"
            r"how\s+about\b|"
            r"let(?:'s| us)\s+(?:discuss|learn|do)\b|now\s+explain\b|"
            r"what\s+is\s+the\s+difference\s+between\b)", lower
        ))

    def _should_switch_context(self, message):
        """Switch only when a self-contained question changes topic.

        Same-topic questions such as "what is the time quantum?" may clarify
        an active exercise, so they remain in that conversation. Pronoun-led
        follow-ups are excluded by _is_standalone_question.
        """
        explicit_family = self._explicit_topic_family(message)
        current_family = self._topic_family(self.last_gap) if self.last_gap else ""
        # A clearly named OS topic wins over stale context even when the
        # sentence starts with a preposition ("In Banker's Algorithm, ...")
        # or is otherwise not a recognized question template.
        if explicit_family and current_family and explicit_family != current_family:
            return True
        if not self._is_standalone_question(message):
            return False
        candidate = self._find_gap(message)
        if not candidate:
            # A self-contained non-OS question should be redirected on its own,
            # not interpreted as an answer to the current OS exercise.
            return True
        if not self.last_gap:
            return True
        return self._topic_family(candidate) != self._topic_family(self.last_gap)

    @classmethod
    def _explicit_topic_family(cls, message):
        lower = message.lower()
        groups = (
            ("deadlocks and resource allocation", r"\bbanker(?:'s)?\b|\bsafe sequence\b|\bneed matrix\b|\bdeadlock\b"),
            ("cpu scheduling", r"\b(cpu scheduling|round robin|fcfs|sjf|srtf|time quantum|preemptive scheduling)\b"),
            ("processes and concurrency", r"\b(pcb|process control block|context switch|semaphore|mutex|monitor|critical section|race condition|thread)\b"),
            ("memory management", r"\b(page fault|page table|paging|page replacement|virtual memory|tlb|segmentation|thrashing)\b"),
            ("file systems", r"\b(file system|filesystem|inode|journaling|directory structure)\b"),
            ("storage and disk", r"\b(disk scheduling|sstf|c-?scan|c-?look|raid|disk head)\b"),
            ("security and protection", r"\b(authentication|authorization|access matrix|capability|malware|virus|worm|protection domain)\b"),
            ("os principles", r"\b(system call|kernel mode|user mode|interrupt|operating system structure)\b"),
            ("virtualization", r"\b(virtual machine|hypervisor|containerization|containers?)\b"),
            ("performance and mobile", r"\b(mobile operating system|mobile os|scalability|os performance)\b"),
        )
        for family, pattern in groups:
            if re.search(pattern, lower):
                return family
        return ""

    @staticmethod
    def _topic_family(topic):
        lower = topic.lower()
        if "banker" in lower or "deadlock" in lower:
            return "deadlocks and resource allocation"
        if "process" in lower or "thread" in lower or "concurrency" in lower:
            return "processes and concurrency"
        if "schedul" in lower or "cpu" in lower:
            return "cpu scheduling"
        if "virtual memory" in lower or "page replacement" in lower or "memory" in lower:
            return "memory management"
        if "file system" in lower or "filesystem" in lower:
            return "file systems"
        if "storage" in lower or "disk" in lower:
            return "storage and disk"
        if "security" in lower or "protection" in lower:
            return "security and protection"
        if "system call" in lower or "os introduction" in lower or "os principles" in lower:
            return "os principles"
        if "virtualization" in lower:
            return "virtualization"
        if "performance" in lower or "mobile" in lower:
            return "performance and mobile"
        return lower.strip()

    @staticmethod
    def _read_banker_need_problem(problem):
        lower = problem.lower()
        if "max" not in lower or "allocation" not in lower:
            return None
        max_match = re.search(r"max(?:imum)?\s*[:=]\s*(\[\[.*?\]\])", problem, re.I | re.S)
        allocation_match = re.search(r"allocation\s*[:=]\s*(\[\[.*?\]\])", problem, re.I | re.S)
        if not max_match or not allocation_match:
            return None
        try:
            maximum = ast.literal_eval(max_match.group(1))
            allocation = ast.literal_eval(allocation_match.group(1))
            if not all(isinstance(row, list) for row in maximum + allocation):
                return None
            expected = calculate_need(maximum, allocation)
            if "safe sequence" in lower or "safe order" in lower:
                available_match = re.search(r"available\s*[:=]\s*(\[[^\[\]]*\])", problem, re.I)
                if available_match:
                    available = ast.literal_eval(available_match.group(1))
                    if len(available) == len(expected[0]):
                        return {
                            "type": "banker_safe", "expected": expected,
                            "maximum": maximum, "allocation": allocation, "available": available,
                        }
            if "need" in lower:
                return {"type": "banker_need", "expected": expected}
            return None
        except (ValueError, SyntaxError, TypeError):
            return None

    def _check_banker_safe_answer(self, problem, response, gap):
        process_ids = [int(value) for value in re.findall(r"\bP\s*(\d+)\b", response, re.I)]
        if not process_ids or self._is_standalone_question(response):
            return None
        task = self.numeric_task
        count = len(task["expected"])
        work = list(task["available"])
        first_blocked = None
        valid = len(process_ids) == count and sorted(process_ids) == list(range(count))
        if valid:
            for process_id in process_ids:
                need = task["expected"][process_id]
                if not all(need_value <= available for need_value, available in zip(need, work)):
                    first_blocked = process_id
                    valid = False
                    break
                work = [value + allocated for value, allocated in zip(work, task["allocation"][process_id])]
        if valid:
            message = "Correct. Each process can run with the resources available at that step, and its allocation is released for the next process."
            self._save_attempt(problem, response, "Correct", message)
            self.last_problem = ""
            self.last_gap = ""
            self.numeric_task = None
            self._save_state()
            return {
                "message": message, "response_type": "feedback", "topic": gap,
                "hint_type": "Correct", "level": 0, "sources": [], "status": "correct",
            }
        if first_blocked is not None:
            message = f"Not quite. P{first_blocked} cannot run at that point with the currently available resources. Check its Need against Available before choosing it."
        else:
            message = f"Not quite. Include every process P0 to P{count - 1} exactly once, then I can check whether the order is safe."
        if self._learning_attempt_count(problem, response) >= SOLUTION_AFTER_ATTEMPTS:
            solution = safe_sequence(task["available"], task["maximum"], task["allocation"])
            message = (
                f"Let's work it through. One safe sequence is {', '.join(solution)}. "
                "At each step, the chosen process has Need no greater than Available; after it finishes, "
                "its Allocation is returned to Available."
                if solution else
                "After checking every process against Available, no process can start, so this state has no safe sequence."
            )
            self._save_attempt(problem, response, "Direct", message)
            self.last_problem = ""
            self.last_gap = ""
            self.numeric_task = None
            self._save_state()
            return {
                "message": message, "response_type": "feedback", "topic": gap,
                "hint_type": "Direct", "level": 0, "sources": [], "status": "solution",
            }
        self._save_attempt(problem, response, "Diagnose", message)
        return {
            "message": message, "response_type": "feedback", "topic": gap,
            "hint_type": "Diagnose", "level": 2, "sources": [], "status": "incorrect",
        }

    def _check_banker_need_answer(self, problem, response, gap):
        match = re.search(r"\[\[.*?\]\]", response, re.S)
        if not match:
            formula = response.lower().replace(" ", "").replace("minus", "-")
            if "need" in formula and "max-allocation" in formula:
                message = "Your formula is correct. Now apply it to each row and send the resulting matrix so I can check the numbers."
                self._save_attempt(problem, response, "Identify", message)
                return {
                    "message": message, "response_type": "feedback", "topic": gap,
                    "hint_type": "Identify", "level": 2, "sources": [], "status": "in_progress",
                }
            lower = response.lower()
            if "need" in lower and ("max + allocation" in lower or "max+allocation" in lower or "add" in lower):
                message = "Not quite. Need is the amount still required. Subtract Allocation from Max for each cell, then send the matrix so I can check the numbers."
                if self._learning_attempt_count(problem, response) >= SOLUTION_AFTER_ATTEMPTS:
                    message = f"Need = Max - Allocation. The correct Need matrix is {self.numeric_task['expected']}. Each entry is calculated by subtracting Allocation from Max in the same row and column."
                    self._save_attempt(problem, response, "Direct", message)
                    self.last_problem = ""
                    self.last_gap = ""
                    self.numeric_task = None
                    self._save_state()
                    return {
                        "message": message, "response_type": "feedback", "topic": gap,
                        "hint_type": "Direct", "level": 0, "sources": [], "status": "solution",
                    }
                self._save_attempt(problem, response, "Diagnose", message)
                return {
                    "message": message, "response_type": "feedback", "topic": gap,
                    "hint_type": "Diagnose", "level": 2, "sources": [], "status": "incorrect",
                }
            return None
        try:
            answer = ast.literal_eval(match.group(0))
        except (ValueError, SyntaxError):
            return None
        expected = self.numeric_task["expected"]
        if answer == expected:
            message = "Correct. Every Need value matches Max minus Allocation in the same row and column. Your matrix is right."
            self._save_attempt(problem, response, "Correct", message)
            self.last_problem = ""
            self.last_gap = ""
            self.numeric_task = None
            self._save_state()
            return {
                "message": message, "response_type": "feedback", "topic": gap,
                "hint_type": "Correct", "level": 0, "sources": [], "status": "correct",
            }
        expected_rows = expected
        for row_index, expected_row in enumerate(expected_rows):
            if row_index >= len(answer) or not isinstance(answer[row_index], list):
                break
            for column_index, expected_value in enumerate(expected_row):
                if column_index >= len(answer[row_index]) or answer[row_index][column_index] != expected_value:
                    process = f"P{row_index}"
                    resource = column_index + 1
                    message = (
                        f"Not quite. In {process}, resource {resource}, check the subtraction again. "
                        "Need is Max minus Allocation for that same cell. Send the corrected matrix when ready."
                    )
                    if self._learning_attempt_count(problem, response) >= SOLUTION_AFTER_ATTEMPTS:
                        message = f"Let's finish it together. The correct Need matrix is {expected}. For each cell, subtract Allocation from Max in the same row and column."
                        self._save_attempt(problem, response, "Direct", message)
                        self.last_problem = ""
                        self.last_gap = ""
                        self.numeric_task = None
                        self._save_state()
                        return {
                            "message": message, "response_type": "feedback", "topic": gap,
                            "hint_type": "Direct", "level": 0, "sources": [], "status": "solution",
                        }
                    self._save_attempt(problem, response, "Diagnose", message)
                    return {
                        "message": message, "response_type": "feedback", "topic": gap,
                        "hint_type": "Diagnose", "level": 2, "sources": [], "status": "incorrect",
                    }
        if self._learning_attempt_count(problem, response) >= SOLUTION_AFTER_ATTEMPTS:
            message = f"The submitted matrix shape does not match the problem. The correct Need matrix is {expected}; calculate each entry as Max minus Allocation in the same cell."
            self._save_attempt(problem, response, "Direct", message)
            self.last_problem = ""
            self.last_gap = ""
            self.numeric_task = None
            self._save_state()
            return {
                "message": message, "response_type": "feedback", "topic": gap,
                "hint_type": "Direct", "level": 0, "sources": [], "status": "solution",
            }
        message = "The matrix shape does not match the Max and Allocation matrices. Check that every process row and resource column is included."
        self._save_attempt(problem, response, "Diagnose", message)
        return {
            "message": message, "response_type": "feedback", "topic": gap,
            "hint_type": "Diagnose", "level": 2, "sources": [], "status": "incorrect",
        }

    def _find_gap(self, text):
        lower = text.lower().replace("\u2212", "-")
        if "need" in lower and ("max + allocation" in lower or "max+allocation" in lower):
            return "Banker's Algorithm Need calculation"
        if "banker" in lower or "safe sequence" in lower or "need matrix" in lower:
            return "Banker's Algorithm"
        if "deadlock" in lower:
            return "deadlocks"
        explicit_family = self._explicit_topic_family(lower)
        explicit_topics = {
            "cpu scheduling": "CPU scheduling",
            "processes and concurrency": "processes and threads",
            "memory management": "page replacement and thrashing" if re.search(
                r"\b(page fault|page replacement|reference string|thrashing)\b", lower
            ) else "memory management",
            "file systems": "file systems",
            "storage and disk": "disk scheduling",
            "security and protection": "security and protection",
            "os principles": "OS principles and system calls",
            "virtualization": "virtualization",
            "performance and mobile": "performance and mobile systems",
        }
        if explicit_family in explicit_topics:
            return explicit_topics[explicit_family]
        return self.retriever.classify_topic(text)

    def history(self):
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT problem, response, hint_type, hint, created_at FROM attempts ORDER BY id DESC LIMIT 20"
            ).fetchall()
        return [dict(row) for row in rows]

    def conversation(self):
        """Return the active transcript so the browser matches saved context."""
        if not self.last_problem:
            return []
        turns = [{"role": "user", "text": self.last_problem}]
        for student_text, assistant_text in self._recent(self.last_problem):
            if student_text:
                turns.append({"role": "user", "text": student_text})
            if assistant_text:
                turns.append({"role": "assistant", "text": assistant_text})
        return turns
