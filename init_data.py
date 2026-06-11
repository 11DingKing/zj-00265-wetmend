from datetime import date
from database import SessionLocal, engine, Base
import models
from models import ProjectStatus, DegradationType, DegradationLevel, AcceptanceResult

Base.metadata.create_all(bind=engine)


def init_sample_data():
    db = SessionLocal()
    try:
        if db.query(models.Project).count() > 0:
            print("数据库已有数据，跳过初始化")
            return

        project1 = models.Project(
            name="青海湖东岸湿地萎缩修复项目",
            region="青海省海北藏族自治州",
            degradation_type=DegradationType.WETLAND_SHRINKAGE,
            degradation_level=DegradationLevel.SEVERE,
            total_restoration_area=500.0,
            restoration_measures="乡土植物补植,微生物调控,外源辅助",
            status=ProjectStatus.ESTABLISHED,
            establishment_date=date(2025, 3, 15),
            target_vegetation_coverage=85.0,
            target_carbon_sequestration=120.0,
            target_water_conservation=500.0,
            description="针对青海湖东岸严重萎缩的湿地进行综合修复"
        )

        project2 = models.Project(
            name="祁连山北麓草地沙化治理项目",
            region="甘肃省张掖市",
            degradation_type=DegradationType.GRASSLAND_DESERTIFICATION,
            degradation_level=DegradationLevel.MODERATE,
            total_restoration_area=800.0,
            restoration_measures="乡土植物补植,微生物调控",
            status=ProjectStatus.IMPLEMENTING,
            establishment_date=date(2025, 1, 10),
            target_vegetation_coverage=80.0,
            target_carbon_sequestration=180.0,
            target_water_conservation=400.0,
            description="祁连山北麓中度沙化草地修复工程"
        )

        project3 = models.Project(
            name="甘南玛曲湿地生态修复项目",
            region="甘肃省甘南藏族自治州",
            degradation_type=DegradationType.WETLAND_SHRINKAGE,
            degradation_level=DegradationLevel.MODERATE,
            total_restoration_area=300.0,
            restoration_measures="乡土植物补植,外源辅助",
            status=ProjectStatus.MONITORING,
            establishment_date=date(2024, 6, 20),
            target_vegetation_coverage=90.0,
            target_carbon_sequestration=100.0,
            target_water_conservation=600.0,
            description="甘南玛曲高原湿地生态系统修复与监测"
        )

        project4 = models.Project(
            name="青海三江源区黑土滩治理项目",
            region="青海省玉树藏族自治州",
            degradation_type=DegradationType.GRASSLAND_DESERTIFICATION,
            degradation_level=DegradationLevel.SEVERE,
            total_restoration_area=1200.0,
            restoration_measures="乡土植物补植,微生物调控,外源辅助",
            status=ProjectStatus.ACCEPTED,
            establishment_date=date(2024, 3, 1),
            target_vegetation_coverage=75.0,
            target_carbon_sequestration=250.0,
            target_water_conservation=350.0,
            description="三江源区严重退化黑土滩综合治理工程"
        )

        project5 = models.Project(
            name="四川若尔盖湿地恢复项目",
            region="四川省阿坝藏族羌族自治州",
            degradation_type=DegradationType.WETLAND_SHRINKAGE,
            degradation_level=DegradationLevel.MILD,
            total_restoration_area=450.0,
            restoration_measures="乡土植物补植",
            status=ProjectStatus.MONITORING,
            establishment_date=date(2024, 9, 5),
            target_vegetation_coverage=88.0,
            target_carbon_sequestration=95.0,
            target_water_conservation=550.0,
            description="若尔盖高原湿地轻度萎缩区域恢复项目"
        )

        db.add_all([project1, project2, project3, project4, project5])
        db.flush()

        plot1_1 = models.Plot(
            project_id=project1.id,
            plot_code="QHH-DS-001",
            location="青海湖东岸鸟岛片区",
            area=200.0,
            degradation_type=DegradationType.WETLAND_SHRINKAGE,
            degradation_level=DegradationLevel.SEVERE
        )
        plot1_2 = models.Plot(
            project_id=project1.id,
            plot_code="QHH-DS-002",
            location="青海湖东岸沙柳河片区",
            area=300.0,
            degradation_type=DegradationType.WETLAND_SHRINKAGE,
            degradation_level=DegradationLevel.SEVERE
        )

        plot2_1 = models.Plot(
            project_id=project2.id,
            plot_code="QLS-SH-001",
            location="祁连山北麓肃南县段",
            area=400.0,
            degradation_type=DegradationType.GRASSLAND_DESERTIFICATION,
            degradation_level=DegradationLevel.MODERATE
        )
        plot2_2 = models.Plot(
            project_id=project2.id,
            plot_code="QLS-SH-002",
            location="祁连山北麓民乐县段",
            area=400.0,
            degradation_type=DegradationType.GRASSLAND_DESERTIFICATION,
            degradation_level=DegradationLevel.MODERATE
        )

        plot3_1 = models.Plot(
            project_id=project3.id,
            plot_code="GN-SD-001",
            location="玛曲县采日玛乡",
            area=150.0,
            degradation_type=DegradationType.WETLAND_SHRINKAGE,
            degradation_level=DegradationLevel.MODERATE
        )
        plot3_2 = models.Plot(
            project_id=project3.id,
            plot_code="GN-SD-002",
            location="玛曲县曼日玛乡",
            area=150.0,
            degradation_type=DegradationType.WETLAND_SHRINKAGE,
            degradation_level=DegradationLevel.MODERATE
        )

        plot4_1 = models.Plot(
            project_id=project4.id,
            plot_code="SJY-HT-001",
            location="玉树州称多县",
            area=600.0,
            degradation_type=DegradationType.GRASSLAND_DESERTIFICATION,
            degradation_level=DegradationLevel.SEVERE
        )
        plot4_2 = models.Plot(
            project_id=project4.id,
            plot_code="SJY-HT-002",
            location="玉树州治多县",
            area=600.0,
            degradation_type=DegradationType.GRASSLAND_DESERTIFICATION,
            degradation_level=DegradationLevel.SEVERE
        )

        plot5_1 = models.Plot(
            project_id=project5.id,
            plot_code="REG-SD-001",
            location="若尔盖县唐克镇",
            area=225.0,
            degradation_type=DegradationType.WETLAND_SHRINKAGE,
            degradation_level=DegradationLevel.MILD
        )
        plot5_2 = models.Plot(
            project_id=project5.id,
            plot_code="REG-SD-002",
            location="若尔盖县辖曼镇",
            area=225.0,
            degradation_type=DegradationType.WETLAND_SHRINKAGE,
            degradation_level=DegradationLevel.MILD
        )

        db.add_all([
            plot1_1, plot1_2,
            plot2_1, plot2_2,
            plot3_1, plot3_2,
            plot4_1, plot4_2,
            plot5_1, plot5_2
        ])
        db.flush()

        imp_records = [
            models.ImplementationRecord(
                plot_id=plot2_1.id,
                record_year=2025,
                record_month=3,
                planted_area=80.0,
                survival_count=15000,
                total_planted_count=16000,
                survival_rate=93.75,
                notes="补植垂穗披碱草，生长状况良好"
            ),
            models.ImplementationRecord(
                plot_id=plot2_1.id,
                record_year=2025,
                record_month=4,
                planted_area=90.0,
                survival_count=17500,
                total_planted_count=18500,
                survival_rate=94.59,
                notes="补植老芒麦，配合微生物菌剂"
            ),
            models.ImplementationRecord(
                plot_id=plot2_1.id,
                record_year=2025,
                record_month=5,
                planted_area=75.0,
                survival_count=14200,
                total_planted_count=15000,
                survival_rate=94.67,
                notes="补植早熟禾"
            ),
            models.ImplementationRecord(
                plot_id=plot2_2.id,
                record_year=2025,
                record_month=3,
                planted_area=85.0,
                survival_count=16000,
                total_planted_count=17200,
                survival_rate=93.02,
                notes="民乐县段首次补植"
            ),
            models.ImplementationRecord(
                plot_id=plot2_2.id,
                record_year=2025,
                record_month=4,
                planted_area=95.0,
                survival_count=18000,
                total_planted_count=19000,
                survival_rate=94.74,
                notes="补植进展顺利"
            ),
            models.ImplementationRecord(
                plot_id=plot2_2.id,
                record_year=2025,
                record_month=5,
                planted_area=70.0,
                survival_count=13800,
                total_planted_count=14500,
                survival_rate=95.17,
                notes="本月补植完成"
            )
        ]
        db.add_all(imp_records)

        mon_records = [
            models.MonitoringRecord(
                plot_id=plot3_1.id,
                record_date=date(2025, 3, 15),
                vegetation_coverage=78.5,
                carbon_sequestration=22.5,
                water_conservation=135.0,
                notes="春季监测，植被恢复良好"
            ),
            models.MonitoringRecord(
                plot_id=plot3_1.id,
                record_date=date(2025, 6, 15),
                vegetation_coverage=83.2,
                carbon_sequestration=28.8,
                water_conservation=156.5,
                notes="夏季监测，指标稳步提升"
            ),
            models.MonitoringRecord(
                plot_id=plot3_2.id,
                record_date=date(2025, 3, 15),
                vegetation_coverage=76.8,
                carbon_sequestration=21.2,
                water_conservation=128.0,
                notes="曼日玛乡片区春季监测"
            ),
            models.MonitoringRecord(
                plot_id=plot3_2.id,
                record_date=date(2025, 6, 15),
                vegetation_coverage=82.5,
                carbon_sequestration=27.5,
                water_conservation=152.0,
                notes="夏季监测成效显著"
            ),
            models.MonitoringRecord(
                plot_id=plot5_1.id,
                record_date=date(2025, 4, 10),
                vegetation_coverage=82.0,
                carbon_sequestration=18.5,
                water_conservation=120.0,
                notes="若尔盖春季监测"
            ),
            models.MonitoringRecord(
                plot_id=plot5_1.id,
                record_date=date(2025, 7, 10),
                vegetation_coverage=86.5,
                carbon_sequestration=24.2,
                water_conservation=145.5,
                notes="夏季监测"
            ),
            models.MonitoringRecord(
                plot_id=plot5_2.id,
                record_date=date(2025, 4, 10),
                vegetation_coverage=80.5,
                carbon_sequestration=17.8,
                water_conservation=115.0,
                notes="辖曼镇片区监测"
            ),
            models.MonitoringRecord(
                plot_id=plot5_2.id,
                record_date=date(2025, 7, 10),
                vegetation_coverage=85.8,
                carbon_sequestration=23.5,
                water_conservation=142.0,
                notes="夏季监测数据"
            )
        ]
        db.add_all(mon_records)

        acceptance = models.Acceptance(
            project_id=project4.id,
            acceptance_date=date(2025, 5, 20),
            result=AcceptanceResult.PASSED,
            final_vegetation_coverage=78.5,
            final_carbon_sequestration=265.0,
            final_water_conservation=380.0,
            extension_days=None,
            remarks="各项指标均达到或超过立项目标，同意通过验收"
        )
        db.add(acceptance)

        db.commit()
        print("初始化数据完成！")
        print(f"创建了 {db.query(models.Project).count()} 个项目")
        print(f"创建了 {db.query(models.Plot).count()} 个地块")
        print(f"创建了 {db.query(models.ImplementationRecord).count()} 条实施记录")
        print(f"创建了 {db.query(models.MonitoringRecord).count()} 条监测记录")
        print(f"创建了 {db.query(models.Acceptance).count()} 条验收记录")

    except Exception as e:
        print(f"初始化数据失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_sample_data()
