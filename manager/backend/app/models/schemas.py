from datetime import datetime
from typing import List, Optional

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore

from pydantic import BaseModel


class ChannelSummary(BaseModel):
    id: str
    name: str
    description: str = ""
    profile: str
    raw_path: str
    extensions: List[str] = []


class ChannelStats(BaseModel):
    id: str
    name: str
    description: str = ""
    profile: str
    raw_path: str
    artifact_count: int = 0
    pending: int = 0


class VaultSummary(BaseModel):
    id: str
    name: str
    path: str
    artifact_count: int = 0
    pdf_count: int = 0
    paper_count: int = 0
    theme_count: int = 0
    last_build: Optional[str] = None
    pending_artifacts: int = 0
    channels: List[ChannelStats] = []


class BuildResponse(BaseModel):
    job_id: str
    mode: str = "auto"
    channel_id: str = "my-portfolio"


class UploadResponse(BaseModel):
    files_added: int
    filenames: List[str]
    channel_id: str = "my-portfolio"
    channel_name: str = ""
    raw_path: str = ""


class JobStatus(BaseModel):
    id: str
    type: str
    vault_id: str
    status: Literal["queued", "running", "completed", "failed"]
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    log_file: Optional[str] = None


class JobLogs(BaseModel):
    job_id: str
    lines: List[str]
    status: str
