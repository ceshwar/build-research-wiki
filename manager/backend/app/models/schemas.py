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
    needs_human_verification: int = 0
    human_verified_count: int = 0
    needs_attention: List[dict] = []
    needs_verification: List[dict] = []


class VaultSummary(BaseModel):
    id: str
    name: str
    path: str
    obsidian_vault_id: Optional[str] = None
    obsidian_links_ok: bool = False
    obsidian_link_path: Optional[str] = None
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
    needs_human_verification_count: int = 0
    human_verified_count: int = 0
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


class VerificationUpdateRequest(BaseModel):
    human_verified: bool
    verified_by: str = "human"


class VerificationUpdateResponse(BaseModel):
    slug: str
    channel_id: str
    human_verified: bool
    verified_at: str = ""
    verified_by: str = ""
    job_id: Optional[str] = None


class LlmConfigResponse(BaseModel):
    ollama_url: str
    default_model: str
    embedding_model: str
    think: bool = False
    stages: dict = {}


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
    human_verified: bool = False
    needs_human_verification: bool = False
    llm_enriched: bool = False
    llm_model: str = ""
    enrichment_source: str = ""
    territory: str = "charted"
    verified_at: str = ""
    verified_by: str = ""


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


class ChartGraphNode(BaseModel):
    id: str
    slug: str
    label: str
    type: str
    wiki_page: str
    status: Optional[str] = None
    human_verified: Optional[bool] = None
    needs_human_verification: Optional[bool] = None


class ChartGraphEdge(BaseModel):
    source: str
    target: str
    kind: str = "link"


class ChartGraphResponse(BaseModel):
    channel_id: str
    nodes: List[ChartGraphNode] = []
    edges: List[ChartGraphEdge] = []
    stats: dict = {}
    message: str = ""


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


class LlmModelsConfig(BaseModel):
    deep_dive: str = "qwen3:32b"
    charting: str = "qwen3:32b"
    query: str = "qwen3:32b"


class FrontierConfig(BaseModel):
    provider: str = "anthropic"
    deep_dive_model: str = "claude-sonnet-4-20250514"
    query_model: str = "claude-sonnet-4-20250514"


class LlmSettings(BaseModel):
    deep_dive_provider: str = "local"
    query_provider: str = "local"
    ollama_url: str = "http://127.0.0.1:11500"
    think: bool = False
    model_catalog: List[str] = []
    models: LlmModelsConfig = LlmModelsConfig()
    frontier: FrontierConfig = FrontierConfig()


class AppSettingsResponse(BaseModel):
    view_in: str = "app"
    llm: LlmSettings = LlmSettings()


class AppSettingsUpdateRequest(BaseModel):
    view_in: Optional[str] = None
    llm: Optional[dict] = None


class DeepDiveRequest(BaseModel):
    slug: Optional[str] = None
    slugs: List[str] = []
    provider: Optional[str] = None
    model: Optional[str] = None


class DeepDiveResponse(BaseModel):
    job_id: str
    model: str = ""
    provider: str = "local"
    slugs: List[str] = []


class QueryRequest(BaseModel):
    question: str
    provider: Optional[str] = None
    model: Optional[str] = None
    scope: str = "all"  # all | verified | needs_review | uncharted


class QueryResponse(BaseModel):
    job_id: str
    model: str = ""
    provider: str = "local"
    question: str = ""


class QueryResultResponse(BaseModel):
    job_id: str
    status: str
    question: str = ""
    answer: str = ""
    model: str = ""
    elapsed_s: Optional[float] = None
    provider_kind: str = ""


class VaultFileResponse(BaseModel):
    path: str
    content_type: str
    content: Optional[str] = None
    size: int = 0
