"""Borradores de la Declaración Responsable guardados en servidor (uno por fila, por usuario)."""

from __future__ import annotations

import time
from typing import Optional

from open_webui.internal.db import Base, get_async_db_context
from pydantic import BaseModel, ConfigDict
from sqlalchemy import JSON, BigInteger, Column, Integer, Text, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

####################
# DB Schema
####################


class DeclaracionBorrador(Base):
    __tablename__ = 'declaracion_borrador'

    id = Column(Text, primary_key=True, unique=True)
    user_id = Column(Text, nullable=False, index=True)

    nombre = Column(Text, nullable=False)
    paso = Column(Integer, nullable=False)
    datos = Column(JSON, nullable=True)
    version = Column(Integer, nullable=False)

    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


####################
# Models / forms
####################


class DeclaracionBorradorModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    nombre: str
    paso: int
    datos: dict
    version: int
    created_at: int  # epoch ns
    updated_at: int  # epoch ns


class DeclaracionBorradorResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nombre: str
    paso: int
    version: int
    created_at: int
    updated_at: int


class DeclaracionBorradorForm(BaseModel):
    nombre: str
    paso: int
    datos: dict


class ConflictoVersion(Exception):
    def __init__(self, actual: DeclaracionBorradorModel):
        super().__init__('version conflict')
        self.actual = actual


class IdEnUso(Exception):
    """El id ya pertenece a otro usuario."""


def _modelo(fila: DeclaracionBorrador) -> DeclaracionBorradorModel:
    modelo = DeclaracionBorradorModel.model_validate(fila)
    modelo.datos = modelo.datos or {}
    return modelo


class DeclaracionBorradorTable:
    async def listar(self, user_id: str, db: Optional[AsyncSession] = None) -> list[DeclaracionBorradorResumen]:
        async with get_async_db_context(db) as db:
            stmt = (
                select(
                    DeclaracionBorrador.id,
                    DeclaracionBorrador.nombre,
                    DeclaracionBorrador.paso,
                    DeclaracionBorrador.version,
                    DeclaracionBorrador.created_at,
                    DeclaracionBorrador.updated_at,
                )
                .filter(DeclaracionBorrador.user_id == user_id)
                .order_by(DeclaracionBorrador.updated_at.desc())
            )
            result = await db.execute(stmt)
            return [DeclaracionBorradorResumen.model_validate(fila) for fila in result.all()]

    async def obtener(
        self, id: str, user_id: str, db: Optional[AsyncSession] = None
    ) -> Optional[DeclaracionBorradorModel]:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(DeclaracionBorrador).filter_by(id=id, user_id=user_id)
            )
            fila = result.scalars().first()
            return _modelo(fila) if fila else None

    async def contar(self, user_id: str, db: Optional[AsyncSession] = None) -> int:
        async with get_async_db_context(db) as db:
            result = await db.execute(
                select(func.count(DeclaracionBorrador.id)).filter(DeclaracionBorrador.user_id == user_id)
            )
            return int(result.scalar() or 0)

    async def crear(
        self,
        id: str,
        user_id: str,
        form: DeclaracionBorradorForm,
        db: Optional[AsyncSession] = None,
    ) -> tuple[DeclaracionBorradorModel, bool]:
        """Devuelve ``(borrador, existente)``; reintentar el mismo id no duplica ni sobrescribe."""
        async with get_async_db_context(db) as db:
            result = await db.execute(select(DeclaracionBorrador).filter_by(id=id))
            fila = result.scalars().first()
            if fila:
                if fila.user_id != user_id:
                    raise IdEnUso(id)
                return _modelo(fila), True

            ahora = time.time_ns()
            fila = DeclaracionBorrador(
                id=id,
                user_id=user_id,
                nombre=form.nombre,
                paso=form.paso,
                datos=form.datos,
                version=1,
                created_at=ahora,
                updated_at=ahora,
            )
            db.add(fila)
            await db.commit()
            await db.refresh(fila)
            return _modelo(fila), False

    async def actualizar(
        self,
        id: str,
        user_id: str,
        form: DeclaracionBorradorForm,
        version_esperada: int,
        db: Optional[AsyncSession] = None,
    ) -> Optional[DeclaracionBorradorModel]:
        """``None`` si no existe; ``ConflictoVersion`` si otra escritura llegó antes."""
        async with get_async_db_context(db) as db:
            result = await db.execute(
                update(DeclaracionBorrador)
                .where(
                    DeclaracionBorrador.id == id,
                    DeclaracionBorrador.user_id == user_id,
                    DeclaracionBorrador.version == version_esperada,
                )
                .values(
                    nombre=form.nombre,
                    paso=form.paso,
                    datos=form.datos,
                    version=DeclaracionBorrador.version + 1,
                    updated_at=time.time_ns(),
                )
            )
            await db.commit()

            actual = await self.obtener(id, user_id, db=db)
            if actual is None:
                return None
            if result.rowcount == 0:
                raise ConflictoVersion(actual)
            return actual

    async def eliminar(self, id: str, user_id: str, db: Optional[AsyncSession] = None) -> bool:
        async with get_async_db_context(db) as db:
            result = await db.execute(delete(DeclaracionBorrador).filter_by(id=id, user_id=user_id))
            await db.commit()
            return result.rowcount > 0

    async def purgar_caducados(self, ttl_dias: int, db: Optional[AsyncSession] = None) -> int:
        if ttl_dias <= 0:
            return 0
        limite = time.time_ns() - ttl_dias * 86_400 * 1_000_000_000
        async with get_async_db_context(db) as db:
            result = await db.execute(delete(DeclaracionBorrador).where(DeclaracionBorrador.updated_at < limite))
            await db.commit()
            return result.rowcount or 0


DeclaracionBorradores = DeclaracionBorradorTable()
