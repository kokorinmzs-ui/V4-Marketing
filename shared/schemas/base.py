"""Base Pydantic model with schema versioning for all Marketing OS v4 schemas."""

from pydantic import BaseModel, Field


class MarketingOSBaseModel(BaseModel):
    """Base model for all Marketing OS v4 contracts.
    
    Every schema in the system must include a schema_version field.
    """

    schema_version: str = Field(default="4.0", description="Schema version for compatibility checks")

    class Config:
        populate_by_name = True
        str_strip_whitespace = True
        validate_assignment = True