"""Export Package schema — the final client deliverable."""

from pydantic import Field

from shared.schemas.base import MarketingOSBaseModel


class ExportPackage(MarketingOSBaseModel):
    """The client package — what the client receives as a ZIP.

    Contains all HTML files and assets for offline use.
    """

    project_name: str = Field(..., min_length=1, description="Project name")
    project_id: str = Field(..., description="Project ID")
    
    # Required files
    dashboard_html: str = Field(
        default="02-EXECUTION-DASHBOARD.html",
        description="Main dashboard filename",
    )
    start_here_html: str = Field(
        default="01-START-HERE.html",
        description="Entry point filename",
    )
    content_library_html: str = Field(
        default="03-CONTENT-LIBRARY.html",
        description="Content library filename",
    )
    sales_scripts_html: str = Field(
        default="04-SALES-SCRIPTS.html",
        description="Sales scripts filename",
    )
    marketing_logic_html: str = Field(
        default="05-MARKETING-LOGIC.html",
        description="Marketing logic explanation filename",
    )
    readme_txt: str = Field(
        default="README.txt",
        description="Instructions filename",
    )
    
    # Quality checks
    offline_ready: bool = Field(
        default=True,
        description="All HTML works without server/internet",
    )
    quality_gate_passed: bool = Field(
        default=False,
        description="All quality checks passed",
    )
    no_empty_blocks: bool = Field(
        default=False,
        description="No sections with empty content",
    )
    copy_buttons_work: bool = Field(
        default=False,
        description="All copy buttons functional",
    )
    tabs_work: bool = Field(
        default=False,
        description="All tabs functional",
    )
    local_storage_works: bool = Field(
        default=False,
        description="Progress saved and restored",
    )
    
    # Metadata
    generated_at: str = Field(default="", description="ISO timestamp")
    package_size_bytes: int = Field(default=0, ge=0, description="ZIP file size")
    total_files: int = Field(default=5, ge=1, description="Number of files in package")