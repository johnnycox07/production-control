import os
import tempfile
from datetime import datetime, timezone, timedelta

from openpyxl import Workbook
from sqlalchemy.orm import joinedload

from src.celery_app import celery_app
from src.core.sync_database import SyncSessionLocal as SyncSession


@celery_app.task(bind=True, max_retries=3)
def generate_batch_report(
    self,
    batch_id: int,
    format: str = "excel",
    user_email: str | None = None,
):
    from src.data.models.batch import Batch
    from src.storage.minio_service import MinIOService

    with SyncSession() as session:
        batch = (
            session.query(Batch)
            .options(joinedload(Batch.products))
            .filter(Batch.id == batch_id)
            .first()
        )

        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        with tempfile.NamedTemporaryFile(
            suffix=".xlsx", delete=False
        ) as tmp:
            tmp_path = tmp.name

        wb = Workbook()

        ws1 = wb.active
        ws1.title = "Информация о партии"
        ws1.append(["Номер партии", batch.batch_number])
        ws1.append(["Дата партии", str(batch.batch_date)])
        ws1.append(["Статус", "Закрыта" if batch.is_closed else "Открыта"])
        ws1.append(["Смена", batch.shift])
        ws1.append(["Бригада", batch.team])
        ws1.append(["Номенклатура", batch.nomenclature])
        ws1.append(["Начало смены", str(batch.shift_start)])
        ws1.append(["Окончание смены", str(batch.shift_end)])

        ws2 = wb.create_sheet("Продукция")
        ws2.append(["ID", "Уникальный код", "Агрегирована", "Дата агрегации"])
        for product in batch.products:
            ws2.append([
                product.id,
                product.unique_code,
                "Да" if product.is_aggregated else "Нет",
                str(product.aggregated_at) if product.aggregated_at else "-",
            ])

        ws3 = wb.create_sheet("Статистика")
        total = len(batch.products)
        agg = sum(1 for p in batch.products if p.is_aggregated)
        ws3.append(["Всего продукции", total])
        ws3.append(["Агрегировано", agg])
        ws3.append(["Осталось", total - agg])
        ws3.append(["Процент выполнения", f"{agg / total * 100:.1f}%" if total else "0%"])

        wb.save(tmp_path)

        minio = MinIOService()
        object_name = f"batch_{batch_id}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_url = minio.upload_file(
            bucket="reports",
            file_path=tmp_path,
            object_name=object_name,
            expires_days=7,
        )

        os.unlink(tmp_path)

    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    return {
        "success": True,
        "file_url": file_url,
        "file_name": object_name,
        "file_size": os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0,
        "expires_at": expires_at.isoformat(),
    }