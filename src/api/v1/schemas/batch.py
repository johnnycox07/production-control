from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.api.v1.schemas.product import ProductResponse


class BatchCreate(BaseModel):
    is_closed: bool = Field(default=False, alias="СтатусЗакрытия")
    task_description: str = Field(..., alias="ПредставлениеЗаданияНаСмену")
    work_center: str = Field(..., alias="РабочийЦентр")
    shift: str = Field(..., alias="Смена")
    team: str = Field(..., alias="Бригада")
    batch_number: int = Field(..., alias="НомерПартии")
    batch_date: date = Field(..., alias="ДатаПартии")
    nomenclature: str = Field(..., alias="Номенклатура")
    ekn_code: str = Field(..., alias="КодЕКН")
    work_center_id: str = Field(..., alias="ИдентификаторРЦ")
    shift_start: datetime = Field(..., alias="ДатаВремяНачалаСмены")
    shift_end: datetime = Field(..., alias="ДатаВремяОкончанияСмены")

    model_config = ConfigDict(populate_by_name=True)


class BatchUpdate(BaseModel):
    is_closed: bool | None = Field(None, alias="СтатусЗакрытия")
    task_description: str | None = Field(None, alias="ПредставлениеЗаданияНаСмену")
    work_center: str | None = Field(None, alias="РабочийЦентр")
    shift: str | None = Field(None, alias="Смена")
    team: str | None = Field(None, alias="Бригада")
    batch_number: int | None = Field(None, alias="НомерПартии")
    batch_date: date | None = Field(None, alias="ДатаПартии")
    nomenclature: str | None = Field(None, alias="Номенклатура")
    ekn_code: str | None = Field(None, alias="КодЕКН")
    work_center_id: str | None = Field(None, alias="ИдентификаторРЦ")
    shift_start: datetime | None = Field(None, alias="ДатаВремяНачалаСмены")
    shift_end: datetime | None = Field(None, alias="ДатаВремяОкончанияСмены")

    model_config = ConfigDict(populate_by_name=True)


class BatchResponse(BaseModel):
    id: int
    is_closed: bool
    batch_number: int
    batch_date: date
    task_description: str
    work_center_id: int
    shift: str
    team: str
    nomenclature: str
    ekn_code: str
    shift_start: datetime
    shift_end: datetime
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    products: list["ProductResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AsyncAggregateRequest(BaseModel):
    unique_codes: list[str]


class ExportRequest(BaseModel):
    format: str = "excel"
    filters: dict = {}


class ExportRequest(BaseModel):
    format: str = "excel"
    filters: dict = {}


class CompareBatchesRequest(BaseModel):
    batch_ids: list[int]