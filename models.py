from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import relationship
from database import Base
import enum


class DegradationType(str, enum.Enum):
    WETLAND_SHRINKAGE = "湿地萎缩"
    GRASSLAND_DESERTIFICATION = "草地沙化"


class DegradationLevel(str, enum.Enum):
    MILD = "轻度"
    MODERATE = "中度"
    SEVERE = "重度"


class ProjectStatus(str, enum.Enum):
    ESTABLISHED = "立项"
    IMPLEMENTING = "实施中"
    MONITORING = "监测期"
    ACCEPTED = "验收"


class RestorationMeasure(str, enum.Enum):
    NATIVE_PLANTING = "乡土植物补植"
    MICROBIAL_REGULATION = "微生物调控"
    EXOGENOUS_ASSISTANCE = "外源辅助"


class AcceptanceResult(str, enum.Enum):
    PASSED = "达标"
    EXTENDED = "需延期整改"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True)
    region = Column(String(200), index=True)
    degradation_type = Column(Enum(DegradationType), index=True)
    degradation_level = Column(Enum(DegradationLevel))
    total_restoration_area = Column(Float)
    restoration_measures = Column(String(500))
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ESTABLISHED)
    establishment_date = Column(Date)
    target_vegetation_coverage = Column(Float)
    target_carbon_sequestration = Column(Float)
    target_water_conservation = Column(Float)
    description = Column(Text, nullable=True)

    plots = relationship("Plot", back_populates="project", cascade="all, delete-orphan")
    acceptance = relationship("Acceptance", back_populates="project", uselist=False)


class Plot(Base):
    __tablename__ = "plots"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    plot_code = Column(String(50), index=True)
    location = Column(String(300))
    area = Column(Float)
    degradation_type = Column(Enum(DegradationType))
    degradation_level = Column(Enum(DegradationLevel))

    project = relationship("Project", back_populates="plots")
    implementation_records = relationship("ImplementationRecord", back_populates="plot", cascade="all, delete-orphan")
    monitoring_records = relationship("MonitoringRecord", back_populates="plot", cascade="all, delete-orphan")


class ImplementationRecord(Base):
    __tablename__ = "implementation_records"

    id = Column(Integer, primary_key=True, index=True)
    plot_id = Column(Integer, ForeignKey("plots.id"))
    record_year = Column(Integer)
    record_month = Column(Integer)
    planted_area = Column(Float)
    survival_count = Column(Integer)
    total_planted_count = Column(Integer)
    survival_rate = Column(Float)
    notes = Column(Text, nullable=True)

    plot = relationship("Plot", back_populates="implementation_records")


class MonitoringRecord(Base):
    __tablename__ = "monitoring_records"

    id = Column(Integer, primary_key=True, index=True)
    plot_id = Column(Integer, ForeignKey("plots.id"))
    record_date = Column(Date)
    vegetation_coverage = Column(Float)
    carbon_sequestration = Column(Float)
    water_conservation = Column(Float)
    notes = Column(Text, nullable=True)

    plot = relationship("Plot", back_populates="monitoring_records")


class Acceptance(Base):
    __tablename__ = "acceptances"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    acceptance_date = Column(Date)
    result = Column(Enum(AcceptanceResult))
    final_vegetation_coverage = Column(Float)
    final_carbon_sequestration = Column(Float)
    final_water_conservation = Column(Float)
    extension_days = Column(Integer, nullable=True)
    remarks = Column(Text, nullable=True)

    project = relationship("Project", back_populates="acceptance")
