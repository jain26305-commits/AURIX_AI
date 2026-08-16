from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class SeriesObservation(BaseModel):
    date: str
    value: Optional[float]
    state: str


class Phase3InputContract(BaseModel):
    entity_id: str
    observed_data: List[SeriesObservation]
    data_quality: Dict[str, Any]
    missing_period_percentage: float
    derived_metrics: Dict[str, Any]
    inferred_classification: Dict[str, Any]
    model_candidates: List[str]
    baseline_contract: str
    limitations: List[str]
    provenance: Dict[str, Any]
