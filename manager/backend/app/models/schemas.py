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
    emoji: str = "📁"
    description: str = ""
    profile: str
    raw_path: str
    extensions: List[str] = []
    chart_support: Literal["full", "preview"] = "full"
    builtin: bool = True
    hidden: bool = False


class DockCreateRequest(BaseModel):
    name: str
    emoji: str = "📁"
    description: str = ""
    profile: str = "ingest"


class ChannelStats(BaseModel):
    id: str
    name: str
    emoji: str = "📁"
    description: str = ""
    profile: str
    raw_path: str
    extensions: List[str] = []
    builtin: bool = True
    hidden: bool = False
    artifact_count: int = 0
    pending: int = 0
    on_chart: int = 0
    scaffolded: int = 0
    charted: int = 0
    processed: int = 0
    quick_dip: int = 0
    needs_deep_dive: int = 0
    needs_review: int = 0
    needs_attention: List[dict] = []


class VaultSummary(BaseModel):
    id: str
    name: str
    path: str
    user_added: bool = False
    artifact_count: int = 0
    pdf_count: int = 0
    paper_count: int = 0
    theme_count: int = 0
    last_build: Optional[str] = None
    pending_artifacts: int = 0
    on_chart: int = 0
    scaffolded_count: int = 0
    charted_count: int = 0
    processed_count: int = 0
    quick_dip_count: int = 0
    needs_deep_dive_count: int = 0
    needs_review_count: int = 0
    channels: List[ChannelStats] = []


class VaultValidateRequest(BaseModel):
    path: str


class VaultValidateResponse(BaseModel):
    ok: bool
    path: str = ""
    has_builder: bool = False
    has_wiki: bool = False
    paper_count: int = 0
    suggested_name: str = ""
    warnings: List[str] = []
    error: str = ""


class VaultAddRequest(BaseModel):
    path: str
    name: Optional[str] = None


class VaultPickFolderResponse(BaseModel):
    path: Optional[str] = None
    cancelled: bool = False


class RemoveFromChartResponse(BaseModel):
    slug: str
    channel_id: str
    deleted_files: List[str] = []
    job_id: Optional[str] = None


class RemoveFromChartBatchRequest(BaseModel):
    slugs: List[str]


class RemoveFromChartBatchResponse(BaseModel):
    channel_id: str
    removed: List[str] = []
    job_id: Optional[str] = None


class BuildResponse(BaseModel):
    job_id: str
    mode: str = "auto"
    channel_id: str = "my-portfolio"


class IngestPromptResponse(BaseModel):
    prompt: str
    count: int
    channel_id: str = "my-portfolio"


class ChartEntry(BaseModel):
    slug: str
    title: str
    status: str
    year: Optional[int] = None
    venue: str = ""
    pdf: str = ""
    pdf_path: str = ""
    themes: List[str] = []
    overview: str = ""
    entry: str = ""
    wiki_page: str = ""


class ChartTheme(BaseModel):
    slug: str
    title: str


class ChartMapResponse(BaseModel):
    channel_id: str
    channel_name: str = ""
    profile: str = "portfolio"
    raw_path: str = "raw/papers"
    wiki_folder: str = "wiki/papers"
    themes: List[ChartTheme] = []
    entries: List[ChartEntry] = []
    raw_files: List[str] = []
    awaiting_chart: List[str] = []


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
