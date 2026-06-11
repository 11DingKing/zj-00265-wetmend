from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from database import engine, get_db, Base
import models
import schemas
from models import ProjectStatus, DegradationType, AcceptanceResult

Base.metadata.create_all(bind=engine)

app = FastAPI(title="青藏高原湿地草地退化修复项目管理系统", description="管理青藏高原东北缘湿地草地退化修复项目")


@app.post("/projects/", response_model=schemas.Project, tags=["项目管理"])
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.get("/projects/", response_model=List[schemas.Project], tags=["项目管理"])
def get_projects(
    skip: int = 0,
    limit: int = 100,
    region: Optional[str] = None,
    degradation_type: Optional[DegradationType] = None,
    status: Optional[ProjectStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Project)
    if region:
        query = query.filter(models.Project.region == region)
    if degradation_type:
        query = query.filter(models.Project.degradation_type == degradation_type)
    if status:
        query = query.filter(models.Project.status == status)
    return query.offset(skip).limit(limit).all()


@app.get("/projects/{project_id}", response_model=schemas.Project, tags=["项目管理"])
def get_project(project_id: int, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return db_project


@app.put("/projects/{project_id}", response_model=schemas.Project, tags=["项目管理"])
def update_project(project_id: int, project_update: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    update_data = project_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.patch("/projects/{project_id}/status", response_model=schemas.Project, tags=["项目管理"])
def update_project_status(project_id: int, status_update: schemas.ProjectStatusUpdate, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    db_project.status = status_update.status
    db.commit()
    db.refresh(db_project)
    return db_project


@app.delete("/projects/{project_id}", tags=["项目管理"])
def delete_project(project_id: int, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(db_project)
    db.commit()
    return {"message": "项目已删除"}


@app.post("/plots/", response_model=schemas.Plot, tags=["地块管理"])
def create_plot(plot: schemas.PlotCreate, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == plot.project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    db_plot = models.Plot(**plot.model_dump())
    db.add(db_plot)
    db.commit()
    db.refresh(db_plot)
    return db_plot


@app.get("/plots/", response_model=List[schemas.Plot], tags=["地块管理"])
def get_plots(project_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(models.Plot)
    if project_id:
        query = query.filter(models.Plot.project_id == project_id)
    return query.offset(skip).limit(limit).all()


@app.get("/plots/{plot_id}", response_model=schemas.Plot, tags=["地块管理"])
def get_plot(plot_id: int, db: Session = Depends(get_db)):
    db_plot = db.query(models.Plot).filter(models.Plot.id == plot_id).first()
    if db_plot is None:
        raise HTTPException(status_code=404, detail="地块不存在")
    return db_plot


@app.post("/implementation-records/", response_model=schemas.ImplementationRecord, tags=["实施记录"])
def create_implementation_record(record: schemas.ImplementationRecordCreate, db: Session = Depends(get_db)):
    db_plot = db.query(models.Plot).filter(models.Plot.id == record.plot_id).first()
    if db_plot is None:
        raise HTTPException(status_code=404, detail="地块不存在")
    db_project = db_plot.project
    if db_project.status != ProjectStatus.IMPLEMENTING:
        raise HTTPException(status_code=400, detail="项目不在实施期，无法录入实施记录")
    db_record = models.ImplementationRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@app.get("/implementation-records/", response_model=List[schemas.ImplementationRecord], tags=["实施记录"])
def get_implementation_records(
    plot_id: Optional[int] = None,
    project_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.ImplementationRecord)
    if plot_id:
        query = query.filter(models.ImplementationRecord.plot_id == plot_id)
    if project_id:
        query = query.join(models.Plot).filter(models.Plot.project_id == project_id)
    if year:
        query = query.filter(models.ImplementationRecord.record_year == year)
    if month:
        query = query.filter(models.ImplementationRecord.record_month == month)
    return query.offset(skip).limit(limit).all()


@app.post("/monitoring-records/", response_model=schemas.MonitoringRecord, tags=["监测记录"])
def create_monitoring_record(record: schemas.MonitoringRecordCreate, db: Session = Depends(get_db)):
    db_plot = db.query(models.Plot).filter(models.Plot.id == record.plot_id).first()
    if db_plot is None:
        raise HTTPException(status_code=404, detail="地块不存在")
    db_project = db_plot.project
    if db_project.status != ProjectStatus.MONITORING:
        raise HTTPException(status_code=400, detail="项目不在监测期，无法录入监测记录")
    db_record = models.MonitoringRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@app.get("/monitoring-records/", response_model=List[schemas.MonitoringRecord], tags=["监测记录"])
def get_monitoring_records(
    plot_id: Optional[int] = None,
    project_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.MonitoringRecord)
    if plot_id:
        query = query.filter(models.MonitoringRecord.plot_id == plot_id)
    if project_id:
        query = query.join(models.Plot).filter(models.Plot.project_id == project_id)
    if start_date:
        query = query.filter(models.MonitoringRecord.record_date >= start_date)
    if end_date:
        query = query.filter(models.MonitoringRecord.record_date <= end_date)
    return query.offset(skip).limit(limit).all()


@app.post("/acceptances/", response_model=schemas.Acceptance, tags=["验收管理"])
def create_acceptance(acceptance: schemas.AcceptanceCreate, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == acceptance.project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if db_project.status != ProjectStatus.MONITORING:
        raise HTTPException(status_code=400, detail="项目不在监测期，无法进行验收")
    db_acceptance = db.query(models.Acceptance).filter(models.Acceptance.project_id == acceptance.project_id).first()
    if db_acceptance:
        raise HTTPException(status_code=400, detail="该项目已有验收记录")
    db_acceptance = models.Acceptance(**acceptance.model_dump())
    db.add(db_acceptance)
    db_project.status = ProjectStatus.ACCEPTED
    db.commit()
    db.refresh(db_acceptance)
    return db_acceptance


@app.get("/acceptances/", response_model=List[schemas.Acceptance], tags=["验收管理"])
def get_acceptances(
    project_id: Optional[int] = None,
    result: Optional[AcceptanceResult] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.Acceptance)
    if project_id:
        query = query.filter(models.Acceptance.project_id == project_id)
    if result:
        query = query.filter(models.Acceptance.result == result)
    return query.offset(skip).limit(limit).all()


@app.get("/statistics/by-region", response_model=List[schemas.StatisticsByRegion], tags=["统计汇总"])
def get_statistics_by_region(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    region_stats = {}
    
    for project in projects:
        region = project.region
        if region not in region_stats:
            region_stats[region] = {
                "region": region,
                "total_projects": 0,
                "total_restoration_area": 0.0,
                "total_carbon_sequestration": 0.0,
                "passed_projects": 0
            }
        region_stats[region]["total_projects"] += 1
        region_stats[region]["total_restoration_area"] += project.total_restoration_area
        
        for plot in project.plots:
            for record in plot.monitoring_records:
                region_stats[region]["total_carbon_sequestration"] += record.carbon_sequestration
        
        if project.acceptance and project.acceptance.result == AcceptanceResult.PASSED:
            region_stats[region]["passed_projects"] += 1
    
    return [schemas.StatisticsByRegion(**stats) for stats in region_stats.values()]


@app.get("/statistics/by-degradation-type", response_model=List[schemas.StatisticsByDegradationType], tags=["统计汇总"])
def get_statistics_by_degradation_type(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    type_stats = {}
    
    for project in projects:
        deg_type = project.degradation_type.value
        if deg_type not in type_stats:
            type_stats[deg_type] = {
                "degradation_type": deg_type,
                "total_projects": 0,
                "total_restoration_area": 0.0,
                "total_carbon_sequestration": 0.0,
                "passed_projects": 0
            }
        type_stats[deg_type]["total_projects"] += 1
        type_stats[deg_type]["total_restoration_area"] += project.total_restoration_area
        
        for plot in project.plots:
            for record in plot.monitoring_records:
                type_stats[deg_type]["total_carbon_sequestration"] += record.carbon_sequestration
        
        if project.acceptance and project.acceptance.result == AcceptanceResult.PASSED:
            type_stats[deg_type]["passed_projects"] += 1
    
    return [schemas.StatisticsByDegradationType(**stats) for stats in type_stats.values()]


@app.get("/", tags=["系统"])
def root():
    return {
        "name": "青藏高原湿地草地退化修复项目管理系统",
        "version": "1.0.0",
        "description": "管理青藏高原东北缘湿地草地退化修复项目，支持项目全生命周期管理",
        "docs": "/docs"
    }
