from database import engine
from sqlalchemy import text, inspect, Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import declarative_base
from database import Base
import models


def migrate():
    inspector = inspect(engine)

    with engine.connect() as conn:
        if "acceptances" in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns("acceptances")]
            if "round" not in cols:
                conn.execute(text("ALTER TABLE acceptances ADD COLUMN \"round\" INTEGER DEFAULT 1"))
                conn.commit()
                print("已为 acceptances 表添加 round 列，默认值为 1")
            else:
                print("acceptances 表已存在 round 列，跳过")
        else:
            print("acceptances 表不存在，将由 Base.metadata.create_all 创建")

    Base.metadata.create_all(bind=engine)
    print("迁移完成：rectification_plans 表已确保创建")


if __name__ == "__main__":
    migrate()
