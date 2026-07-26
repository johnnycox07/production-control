from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from ...core.database import Base


class WorkCenter(Base):
    __tablename__ = "work_centers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    identifier: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        nullable=False,
    )

    batches: Mapped[list["Batch"]] = relationship(
        back_populates="work_center",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )