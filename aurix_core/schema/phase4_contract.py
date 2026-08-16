from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ForecastPoint(BaseModel):
    date: str
    point_forecast: float
    raw_model_forecast: float
    constraint_applied: bool
    constraint_reason: Optional[str] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    interval_status: str


class ModelEvaluation(BaseModel):
    model_id: str
    status: str
    reason: str
    folds_tested: int
    wape: Optional[float] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    bias: Optional[float] = None
    stability_variance: Optional[float] = None
    baseline_improvement_pct: Optional[float] = None


class Phase4InputContract(BaseModel):
    entity_id: str
    forecast_status: str
    champion_model: Optional[str] = None
    forecast_horizon: int
    forecast: List[ForecastPoint]
    selection_reason: Optional[str] = None
    baseline_model: Optional[str] = None
    model_competition: List[ModelEvaluation]
    data_quality_flags: List[str]
    limitations: List[str]
    provenance: Dict[str, Any]
