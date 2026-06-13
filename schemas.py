from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from models import DegradationType, DegradationLevel, ProjectStatus, AcceptanceResult, RestorationMeasure


class ImplementationRecordBase(BaseModel):
    record_year: int
    record_month: int
    planted_area: float
    survival_count: int
    total_planted_count: int
    survival_rate: float
    notes: Optional[str] = None


class ImplementationRecordCreate(ImplementationRecordBase):
    plot_id: int


class ImplementationRecord(ImplementationRecordBase):
    id: int
    plot_id: int

    class Config:
        from_attributes = True


class MonitoringRecordBase(BaseModel):
    record_date: date
    vegetation_coverage: float
    carbon_sequestration: float
    water_conservation: float
    notes: Optional[str] = None


class MonitoringRecordCreate(MonitoringRecordBase):
    plot_id: int


class MonitoringRecord(MonitoringRecordBase):
    id: int
    plot_id: int

    class Config:
        from_attributes = True


class PlotBase(BaseModel):
    plot_code: str
    location: str
    area: float
    degradation_type: DegradationType
    degradation_level: DegradationLevel


class PlotCreate(PlotBase):
    project_id: int


class Plot(PlotBase):
    id: int
    project_id: int
    implementation_records: List[ImplementationRecord] = []
    monitoring_records: List[MonitoringRecord] = []

    class Config:
        from_attributes = True


class IndicatorComparison(BaseModel):
    indicator_name: str
    target_value: float
    actual_value: float
    reached: bool


class AcceptanceBase(BaseModel):
    acceptance_date: date
    extension_days: Optional[int] = None
    remarks: Optional[str] = None


class AcceptanceCreate(AcceptanceBase):
    project_id: int


class Acceptance(AcceptanceBase):
    id: int
    project_id: int
    round: int
    result: AcceptanceResult
    final_vegetation_coverage: float
    final_carbon_sequestration: float
    final_water_conservation: float
    comparisons: List[IndicatorComparison] = []

    class Config:
        from_attributes = True


class AcceptancePreview(BaseModel):
    project_id: int
    project_name: str
    target_vegetation_coverage: float
    target_carbon_sequestration: float
    target_water_conservation: float
    final_vegetation_coverage: float
    final_carbon_sequestration: float
    final_water_conservation: float
    comparisons: List[IndicatorComparison]
    overall_reached: bool
    can_accept: bool
    reason: Optional[str] = None


class RestorationMeasureRecordBase(BaseModel):
    measure_type: RestorationMeasure
    implementation_area: float
    implementation_date: date
    cost: Optional[float] = None
    contractor: Optional[str] = None
    notes: Optional[str] = None


class RestorationMeasureRecordCreate(RestorationMeasureRecordBase):
    project_id: int


class RestorationMeasureRecordUpdate(BaseModel):
    measure_type: Optional[RestorationMeasure] = None
    implementation_area: Optional[float] = None
    implementation_date: Optional[date] = None
    cost: Optional[float] = None
    contractor: Optional[str] = None
    notes: Optional[str] = None


class RestorationMeasureRecord(RestorationMeasureRecordBase):
    id: int
    project_id: int

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    name: str
    region: str
    degradation_type: DegradationType
    degradation_level: DegradationLevel
    total_restoration_area: float
    restoration_measures: str
    establishment_date: date
    target_vegetation_coverage: float
    target_carbon_sequestration: float
    target_water_conservation: float
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    degradation_type: Optional[DegradationType] = None
    degradation_level: Optional[DegradationLevel] = None
    total_restoration_area: Optional[float] = None
    restoration_measures: Optional[str] = None
    status: Optional[ProjectStatus] = None
    establishment_date: Optional[date] = None
    target_vegetation_coverage: Optional[float] = None
    target_carbon_sequestration: Optional[float] = None
    target_water_conservation: Optional[float] = None
    description: Optional[str] = None


class RectificationPlanBase(BaseModel):
    plan_content: str
    rectification_deadline: date
    responsible_person: Optional[str] = None
    notes: Optional[str] = None


class RectificationPlanCreate(RectificationPlanBase):
    project_id: int
    acceptance_id: int


class RectificationPlanUpdate(BaseModel):
    plan_content: Optional[str] = None
    rectification_deadline: Optional[date] = None
    responsible_person: Optional[str] = None
    completion_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class RectificationPlan(RectificationPlanBase):
    id: int
    project_id: int
    acceptance_id: int
    created_at: date
    completion_date: Optional[date] = None
    status: str

    class Config:
        from_attributes = True


class Project(ProjectBase):
    id: int
    status: ProjectStatus
    plots: List[Plot] = []
    acceptances: List[Acceptance] = []
    measure_records: List[RestorationMeasureRecord] = []
    rectification_plans: List[RectificationPlan] = []

    class Config:
        from_attributes = True


class ProjectStatusUpdate(BaseModel):
    status: ProjectStatus


class StatisticsByRegion(BaseModel):
    region: str
    total_projects: int
    total_restoration_area: float
    total_carbon_sequestration: float
    passed_projects: int


class StatisticsByDegradationType(BaseModel):
    degradation_type: str
    total_projects: int
    total_restoration_area: float
    total_carbon_sequestration: float
    passed_projects: int


class MeasureEffectivenessItem(BaseModel):
    measure_type: str
    total_projects: int
    total_implementation_area: float
    avg_vegetation_coverage: float
    avg_carbon_sequestration: float
    avg_carbon_per_unit_area: float
    avg_water_conservation: float
    avg_target_reach_rate: float
    total_passed_projects: int
    pass_rate: float


class MeasureEffectivenessComparison(BaseModel):
    summary: str
    data: List[MeasureEffectivenessItem]


class ProjectWithMeasures(ProjectBase):
    id: int
    status: ProjectStatus
    plots: List[Plot] = []
    acceptances: List[Acceptance] = []
    measure_records: List[RestorationMeasureRecord] = []
    rectification_plans: List[RectificationPlan] = []

    class Config:
        from_attributes = True
