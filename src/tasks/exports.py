import csv
import os
import tempfile
from datetime import datetime, timezone, timedelta, date

import openpyxl
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.celery_app import celery_app
from src.core.config import settings

sync_engine = create_engine(
    settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
)
SyncSession = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
)


@celery_app.task
def export_batches_to_file(filters: dict, export_format: str = "excel"):
    from src.data.models.batch import Batch
    from src.storage.minio_service import MinIOService

    with SyncSession() as session:
        query = select(Batch)

        if filters.get("is_closed") is not None:
            query = query.where(Batch.is_closed.is_(filters["is_closed"]))

        if filters.get("date_from"):
            query = query.where(
                Batch.batch_date >= date.fromisoformat(filters["date_from"])
            )

        if filters.get("date_to"):
            query = query.where(
                Batch.batch_date <= date.fromisoformat(filters["date_to"])
            )

        if filters.get("work_center_id"):
            query = query.where(
                Batch.work_center_id == filters["work_center_id"]
            )

        batches = session.execute(query).scalars().all()

    if export_format not in ("excel", "csv"):
        raise ValueError(f"Unsupported export format: {export_format}")
    
    if export_format == "csv":
        suffix = ".csv"
        object_name = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    else:
        suffix = ".xlsx"
        object_name = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name

    if export_format == "csv":
        with open(tmp_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Номер партии", "Дата партии", "Статус",
                "Номенклатура", "Код ЕКН", "Смена", "Бригада",
                "Начало смены", "Окончание смены",
            ])
            for batch in batches:
                writer.writerow([
                    batch.id,
                    batch.batch_number,
                    str(batch.batch_date),
                    "Закрыта" if batch.is_closed else "Открыта",
                    batch.nomenclature,
                    batch.ekn_code,
                    batch.shift,
                    batch.team,
                    str(batch.shift_start),
                    str(batch.shift_end),
                ])
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Партии"
        ws.append([
            "ID", "Номер партии", "Дата партии", "Статус",
            "Номенклатура", "Код ЕКН", "Смена", "Бригада",
            "Начало смены", "Окончание смены",
        ])
        for batch in batches:
            ws.append([
                batch.id,
                batch.batch_number,
                str(batch.batch_date),
                "Закрыта" if batch.is_closed else "Открыта",
                batch.nomenclature,
                batch.ekn_code,
                batch.shift,
                batch.team,
                str(batch.shift_start),
                str(batch.shift_end),
            ])
        wb.save(tmp_path)

    minio = MinIOService()
    try:
        file_url = minio.upload_file(
            bucket="exports",
            file_path=tmp_path,
            object_name=object_name,
            expires_days=7,
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {
        "success": True,
        "file_url": file_url,
        "total_batches": len(batches),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    }