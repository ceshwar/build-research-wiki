"""Run subprocesses and capture stdout/stderr to log files."""

import subprocess
import threading
import uuid
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

BACKEND_DIR = Path(__file__).resolve().parents[2]
LOGS_DIR = BACKEND_DIR / "logs"


class ProcessManager:
    def __init__(self) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self._jobs = {}  # type: Dict[str, dict]

    def start(self, job_type, vault_id, command, cwd):
        # type: (str, str, List[str], str) -> str
        job_id = str(uuid.uuid4())[:8]
        log_path = LOGS_DIR / f"{job_id}.log"

        job = {
            "id": job_id,
            "type": job_type,
            "vault_id": vault_id,
            "status": "queued",
            "started_at": None,
            "ended_at": None,
            "exit_code": None,
            "log_file": str(log_path),
            "command": command,
            "cwd": cwd,
        }
        self._jobs[job_id] = job

        thread = threading.Thread(target=self._run, args=(job_id, command, cwd, log_path), daemon=True)
        thread.start()
        return job_id

    def start_chain(self, job_type, vault_id, steps, label=""):
        # type: (str, str, list, str) -> str
        """Run multiple commands sequentially in one job log."""
        job_id = str(uuid.uuid4())[:8]
        log_path = LOGS_DIR / "{}.log".format(job_id)

        job = {
            "id": job_id,
            "type": job_type,
            "vault_id": vault_id,
            "status": "queued",
            "started_at": None,
            "ended_at": None,
            "exit_code": None,
            "log_file": str(log_path),
            "command": [s[1] for s in steps],
            "cwd": steps[0][2] if steps else "",
        }
        self._jobs[job_id] = job

        thread = threading.Thread(
            target=self._run_chain, args=(job_id, steps, log_path, label), daemon=True
        )
        thread.start()
        return job_id

    def _run_chain(self, job_id, steps, log_path, label):
        # type: (str, list, Path, str) -> None
        job = self._jobs[job_id]
        job["status"] = "running"
        job["started_at"] = datetime.now(timezone.utc)
        final_code = 0

        with open(log_path, "w") as log:
            if label:
                log.write("=== {} ===\n\n".format(label))
            for phase, command, cwd in steps:
                log.write("--- phase: {} ---\n".format(phase))
                log.write("$ {}\n".format(" ".join(command)))
                log.write("cwd: {}\n\n".format(cwd))
                log.flush()

                proc = subprocess.Popen(
                    command,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env={**os.environ, "PYTHONUNBUFFERED": "1"},
                )
                for line in proc.stdout:
                    log.write(line)
                    log.flush()
                proc.wait()
                log.write("\n")
                if proc.returncode != 0:
                    final_code = proc.returncode
                    log.write("phase '{}' failed (exit {})\n".format(phase, proc.returncode))
                    break

        job["exit_code"] = final_code
        job["ended_at"] = datetime.now(timezone.utc)
        job["status"] = "completed" if final_code == 0 else "failed"

    def _run(self, job_id, command, cwd, log_path):
        # type: (str, List[str], str, Path) -> None
        job = self._jobs[job_id]
        job["status"] = "running"
        job["started_at"] = datetime.now(timezone.utc)

        with open(log_path, "w") as log:
            log.write(f"$ {' '.join(command)}\n")
            log.write(f"cwd: {cwd}\n\n")
            log.flush()

            proc = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )

            for line in proc.stdout:
                log.write(line)
                log.flush()

            proc.wait()
            job["exit_code"] = proc.returncode
            job["ended_at"] = datetime.now(timezone.utc)
            job["status"] = "completed" if proc.returncode == 0 else "failed"

    def get(self, job_id: str) -> Optional[dict]:
        return self._jobs.get(job_id)

    def read_logs(self, job_id: str, tail=200):
        # type: (str, int) -> List[str]
        job = self._jobs.get(job_id)
        if not job or not job.get("log_file"):
            return []
        log_path = Path(job["log_file"])
        if not log_path.exists():
            return []
        lines = log_path.read_text().splitlines()
        return lines[-tail:]

    def list_recent(self, limit=10):
        # type: (int) -> List[dict]
        jobs = sorted(
            self._jobs.values(),
            key=lambda j: j.get("started_at") or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return jobs[:limit]


process_manager = ProcessManager()
