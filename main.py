from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import date

from database import engine, get_db, Base
import models
import schemas
from models import ProjectStatus, DegradationType, AcceptanceResult

Base.metadata.create_all(bind=engine)

app = FastAPI(title="青藏高原湿地草地退化修复项目管理系统", description="管理青藏高原东北缘湿地草地退化修复项目")


def _calculate_project_final_indicators(db_project: models.Project) -> Optional[Tuple[float, float, float]]:
    total_area = 0.0
    weighted_vegetation = 0.0
    total_carbon = 0.0
    total_water = 0.0
    has_any_data = False

    for plot in db_project.plots:
        if not plot.monitoring_records:
            continue
        latest = max(plot.monitoring_records, key=lambda r: r.record_date)
        has_any_data = True
        total_area += plot.area
        weighted_vegetation += latest.vegetation_coverage * plot.area
        total_carbon += latest.carbon_sequestration
        total_water += latest.water_conservation

    if not has_any_data:
        return None

    final_vegetation = weighted_vegetation / total_area if total_area > 0 else 0.0
    return round(final_vegetation, 2), round(total_carbon, 2), round(total_water, 2)


def _build_comparisons(
    target_veg: float,
    target_carbon: float,
    target_water: float,
    actual_veg: float,
    actual_carbon: float,
    actual_water: float,
) -> List[schemas.IndicatorComparison]:
    return [
        schemas.IndicatorComparison(
            indicator_name="植被覆盖度(%)",
            target_value=target_veg,
            actual_value=actual_veg,
            reached=actual_veg >= target_veg,
        ),
        schemas.IndicatorComparison(
            indicator_name="固碳量(吨)",
            target_value=target_carbon,
            actual_value=actual_carbon,
            reached=actual_carbon >= target_carbon,
        ),
        schemas.IndicatorComparison(
            indicator_name="水源涵养量(万立方米)",
            target_value=target_water,
            actual_value=actual_water,
            reached=actual_water >= target_water,
        ),
    ]


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


@app.get("/acceptances/preview/{project_id}", response_model=schemas.AcceptancePreview, tags=["验收管理"])
def get_acceptance_preview(project_id: int, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="项目不存在")

    can_accept = True
    reason = None

    if db_project.status != ProjectStatus.MONITORING:
        can_accept = False
        reason = "项目不在监测期，无法进行验收"

    db_existing = db.query(models.Acceptance).filter(models.Acceptance.project_id == project_id).first()
    if db_existing:
        can_accept = False
        reason = "该项目已有验收记录"

    indicators = _calculate_project_final_indicators(db_project)
    if indicators is None:
        can_accept = can_accept and False
        reason = reason or "项目下暂无监测记录，无法进行验收"
        actual_veg, actual_carbon, actual_water = 0.0, 0.0, 0.0
    else:
        actual_veg, actual_carbon, actual_water = indicators

    comparisons = _build_comparisons(
        db_project.target_vegetation_coverage,
        db_project.target_carbon_sequestration,
        db_project.target_water_conservation,
        actual_veg,
        actual_carbon,
        actual_water,
    )
    overall_reached = all(c.reached for c in comparisons) if indicators is not None else False

    return schemas.AcceptancePreview(
        project_id=db_project.id,
        project_name=db_project.name,
        target_vegetation_coverage=db_project.target_vegetation_coverage,
        target_carbon_sequestration=db_project.target_carbon_sequestration,
        target_water_conservation=db_project.target_water_conservation,
        final_vegetation_coverage=actual_veg,
        final_carbon_sequestration=actual_carbon,
        final_water_conservation=actual_water,
        comparisons=comparisons,
        overall_reached=overall_reached,
        can_accept=can_accept,
        reason=reason,
    )


@app.post("/acceptances/", response_model=schemas.Acceptance, tags=["验收管理"])
def create_acceptance(acceptance: schemas.AcceptanceCreate, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == acceptance.project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if db_project.status != ProjectStatus.MONITORING:
        raise HTTPException(status_code=400, detail="项目不在监测期，无法进行验收")
    db_existing = db.query(models.Acceptance).filter(models.Acceptance.project_id == acceptance.project_id).first()
    if db_existing:
        raise HTTPException(status_code=400, detail="该项目已有验收记录")

    indicators = _calculate_project_final_indicators(db_project)
    if indicators is None:
        raise HTTPException(status_code=400, detail="项目下暂无监测记录，无法进行验收")

    actual_veg, actual_carbon, actual_water = indicators
    comparisons = _build_comparisons(
        db_project.target_vegetation_coverage,
        db_project.target_carbon_sequestration,
        db_project.target_water_conservation,
        actual_veg,
        actual_carbon,
        actual_water,
    )
    overall_reached = all(c.reached for c in comparisons)
    result = AcceptanceResult.PASSED if overall_reached else AcceptanceResult.EXTENDED

    db_acceptance = models.Acceptance(
        project_id=acceptance.project_id,
        acceptance_date=acceptance.acceptance_date,
        result=result,
        final_vegetation_coverage=actual_veg,
        final_carbon_sequestration=actual_carbon,
        final_water_conservation=actual_water,
        extension_days=acceptance.extension_days,
        remarks=acceptance.remarks,
    )
    db.add(db_acceptance)
    db_project.status = ProjectStatus.ACCEPTED
    db.commit()
    db.refresh(db_acceptance)

    acceptance_data = schemas.Acceptance.model_validate(db_acceptance)
    acceptance_data.comparisons = comparisons
    return acceptance_data


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
    db_acceptances = query.offset(skip).limit(limit).all()

    result_list = []
    for acc in db_acceptances:
        project = acc.project
        comparisons = _build_comparisons(
            project.target_vegetation_coverage,
            project.target_carbon_sequestration,
            project.target_water_conservation,
            acc.final_vegetation_coverage,
            acc.final_carbon_sequestration,
            acc.final_water_conservation,
        )
        acc_data = schemas.Acceptance.model_validate(acc)
        acc_data.comparisons = comparisons
        result_list.append(acc_data)
    return result_list


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
                "passed_projects": 0,
            }
        region_stats[region]["total_projects"] += 1
        region_stats[region]["total_restoration_area"] += project.total_restoration_area

        if project.acceptance:
            region_stats[region]["total_carbon_sequestration"] += project.acceptance.final_carbon_sequestration
            if project.acceptance.result == AcceptanceResult.PASSED:
                region_stats[region]["passed_projects"] += 1
        else:
            indicators = _calculate_project_final_indicators(project)
            if indicators is not None:
                _, actual_carbon, _ = indicators
                region_stats[region]["total_carbon_sequestration"] += actual_carbon

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
                "passed_projects": 0,
            }
        type_stats[deg_type]["total_projects"] += 1
        type_stats[deg_type]["total_restoration_area"] += project.total_restoration_area

        if project.acceptance:
            type_stats[deg_type]["total_carbon_sequestration"] += project.acceptance.final_carbon_sequestration
            if project.acceptance.result == AcceptanceResult.PASSED:
                type_stats[deg_type]["passed_projects"] += 1
        else:
            indicators = _calculate_project_final_indicators(project)
            if indicators is not None:
                _, actual_carbon, _ = indicators
                type_stats[deg_type]["total_carbon_sequestration"] += actual_carbon

    return [schemas.StatisticsByDegradationType(**stats) for stats in type_stats.values()]


def _get_project_actual_indicators(db_project: models.Project) -> Optional[Tuple[float, float, float, float]]:
    indicators = _calculate_project_final_indicators(db_project)
    if indicators is None:
        if db_project.acceptance:
            actual_veg = db_project.acceptance.final_vegetation_coverage
            actual_carbon = db_project.acceptance.final_carbon_sequestration
            actual_water = db_project.acceptance.final_water_conservation
        else:
            return None
    else:
        actual_veg, actual_carbon, actual_water = indicators
    target_veg = db_project.target_vegetation_coverage
    target_carbon = db_project.target_carbon_sequestration
    target_water = db_project.target_water_conservation
    reach_count = 0
    reach_total = 0
    if target_veg and target_veg > 0:
        reach_count += 1 if actual_veg >= target_veg else 0
        reach_total += 1
    if target_carbon and target_carbon > 0:
        reach_count += 1 if actual_carbon >= target_carbon else 0
        reach_total += 1
    if target_water and target_water > 0:
        reach_count += 1 if actual_water >= target_water else 0
        reach_total += 1
    target_reach_rate = (reach_count / reach_total * 100) if reach_total > 0 else 0.0
    return actual_veg, actual_carbon, actual_water, target_reach_rate


@app.post("/measure-records/", response_model=schemas.RestorationMeasureRecord, tags=["措施管理"])
def create_measure_record(record: schemas.RestorationMeasureRecordCreate, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == record.project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if db_project.status not in [ProjectStatus.ESTABLISHED, ProjectStatus.IMPLEMENTING]:
        raise HTTPException(status_code=400, detail="项目状态不在立项或实施期，无法登记措施")
    db_record = models.RestorationMeasureRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@app.get("/measure-records/", response_model=List[schemas.RestorationMeasureRecord], tags=["措施管理"])
def get_measure_records(
    project_id: Optional[int] = None,
    measure_type: Optional[models.RestorationMeasure] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.RestorationMeasureRecord)
    if project_id:
        query = query.filter(models.RestorationMeasureRecord.project_id == project_id)
    if measure_type:
        query = query.filter(models.RestorationMeasureRecord.measure_type == measure_type)
    return query.offset(skip).limit(limit).all()


@app.get("/measure-records/{record_id}", response_model=schemas.RestorationMeasureRecord, tags=["措施管理"])
def get_measure_record(record_id: int, db: Session = Depends(get_db)):
    db_record = db.query(models.RestorationMeasureRecord).filter(models.RestorationMeasureRecord.id == record_id).first()
    if db_record is None:
        raise HTTPException(status_code=404, detail="措施记录不存在")
    return db_record


@app.put("/measure-records/{record_id}", response_model=schemas.RestorationMeasureRecord, tags=["措施管理"])
def update_measure_record(record_id: int, record_update: schemas.RestorationMeasureRecordUpdate, db: Session = Depends(get_db)):
    db_record = db.query(models.RestorationMeasureRecord).filter(models.RestorationMeasureRecord.id == record_id).first()
    if db_record is None:
        raise HTTPException(status_code=404, detail="措施记录不存在")
    update_data = record_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_record, key, value)
    db.commit()
    db.refresh(db_record)
    return db_record


@app.delete("/measure-records/{record_id}", tags=["措施管理"])
def delete_measure_record(record_id: int, db: Session = Depends(get_db)):
    db_record = db.query(models.RestorationMeasureRecord).filter(models.RestorationMeasureRecord.id == record_id).first()
    if db_record is None:
        raise HTTPException(status_code=404, detail="措施记录不存在")
    db.delete(db_record)
    db.commit()
    return {"message": "措施记录已删除"}


@app.get("/statistics/by-measure-effectiveness", response_model=schemas.MeasureEffectivenessComparison, tags=["统计汇总"])
def get_statistics_by_measure_effectiveness(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()

    measure_stats = {}
    for project in projects:
        indicators = _get_project_actual_indicators(project)
        if indicators is None:
            actual_veg, actual_carbon, actual_water, reach_rate = 0.0, 0.0, 0.0, 0.0
            has_data = False
        else:
            actual_veg, actual_carbon, actual_water, reach_rate = indicators
            has_data = True

        passed = False
        if project.acceptance and project.acceptance.result == AcceptanceResult.PASSED:
            passed = True

        used_measure_types = set()
        if project.measure_records:
            for mr in project.measure_records:
                mt = mr.measure_type.value
                used_measure_types.add(mt)
                if mt not in measure_stats:
                    measure_stats[mt] = {
                        "measure_type": mt,
                        "project_ids": set(),
                        "total_implementation_area": 0.0,
                        "vegetation_coverage_values": [],
                        "carbon_sequestration_values": [],
                        "carbon_per_unit_area_values": [],
                        "water_conservation_values": [],
                        "target_reach_rates": [],
                        "passed_count": 0,
                        "has_data_count": 0,
                    }
                measure_stats[mt]["total_implementation_area"] += mr.implementation_area
                measure_stats[mt]["project_ids"].add(project.id)
                if has_data:
                    measure_stats[mt]["has_data_count"] += 1
                    measure_stats[mt]["vegetation_coverage_values"].append(actual_veg)
                    measure_stats[mt]["carbon_sequestration_values"].append(actual_carbon)
                    if project.total_restoration_area > 0:
                        measure_stats[mt]["carbon_per_unit_area_values"].append(actual_carbon / project.total_restoration_area)
                    measure_stats[mt]["water_conservation_values"].append(actual_water)
                    measure_stats[mt]["target_reach_rates"].append(reach_rate)
                if passed:
                    measure_stats[mt]["passed_count"] += 1
        else:
            continue

    result_data = []
    for mt, stats in measure_stats.items():
        total_projects = len(stats["project_ids"])
        has_data_count = stats["has_data_count"]
        avg_veg = round(sum(stats["vegetation_coverage_values"]) / has_data_count, 2) if has_data_count > 0 else 0.0
        avg_carbon = round(sum(stats["carbon_sequestration_values"]) / has_data_count, 2) if has_data_count > 0 else 0.0
        avg_carbon_per_area = round(sum(stats["carbon_per_unit_area_values"]) / has_data_count, 4) if has_data_count > 0 else 0.0
        avg_water = round(sum(stats["water_conservation_values"]) / has_data_count, 2) if has_data_count > 0 else 0.0
        avg_reach = round(sum(stats["target_reach_rates"]) / has_data_count, 2) if has_data_count > 0 else 0.0
        pass_rate = round(stats["passed_count"] / total_projects * 100, 2) if total_projects > 0 else 0.0

        result_data.append(schemas.MeasureEffectivenessItem(
            measure_type=mt,
            total_projects=total_projects,
            total_implementation_area=round(stats["total_implementation_area"], 2),
            avg_vegetation_coverage=avg_veg,
            avg_carbon_sequestration=avg_carbon,
            avg_carbon_per_unit_area=avg_carbon_per_area,
            avg_water_conservation=avg_water,
            avg_target_reach_rate=avg_reach,
            total_passed_projects=stats["passed_count"],
            pass_rate=pass_rate,
        ))

    result_data.sort(key=lambda x: x.avg_carbon_sequestration, reverse=True)

    if result_data:
        top = result_data[0]
        summary = f"共统计 {len(result_data)} 类修复措施，{top.measure_type} 的平均固碳量最高（{top.avg_carbon_sequestration}吨/项目），达标通过率 {top.pass_rate}%。"
    else:
        summary = "暂无足够的措施-监测数据用于成效对比。"

    return schemas.MeasureEffectivenessComparison(summary=summary, data=result_data)


@app.get("/projects/{project_id}/measures-with-effect", tags=["措施管理"])
def get_project_measures_with_effect(project_id: int, db: Session = Depends(get_db)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="项目不存在")

    indicators = _get_project_actual_indicators(db_project)
    if indicators:
        actual_veg, actual_carbon, actual_water, reach_rate = indicators
    else:
        actual_veg, actual_carbon, actual_water, reach_rate = None, None, None, None

    measure_list = []
    for mr in db_project.measure_records:
        measure_list.append({
            "id": mr.id,
            "measure_type": mr.measure_type.value,
            "implementation_area": mr.implementation_area,
            "implementation_date": str(mr.implementation_date),
            "cost": mr.cost,
            "contractor": mr.contractor,
            "notes": mr.notes,
        })

    passed = None
    if db_project.acceptance:
        passed = db_project.acceptance.result.value

    return {
        "project_id": db_project.id,
        "project_name": db_project.name,
        "status": db_project.status.value,
        "measures": measure_list,
        "effect": {
            "actual_vegetation_coverage": actual_veg,
            "actual_carbon_sequestration": actual_carbon,
            "actual_water_conservation": actual_water,
            "target_reach_rate": reach_rate,
            "acceptance_result": passed,
        }
    }


@app.get("/", tags=["系统"])
def root():
    return {
        "name": "青藏高原湿地草地退化修复项目管理系统",
        "version": "1.1.0",
        "description": "管理青藏高原东北缘湿地草地退化修复项目，支持项目全生命周期管理、措施登记与成效对比",
        "docs": "/docs"
    }
