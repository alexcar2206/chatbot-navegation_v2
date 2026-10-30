import asyncio
import time
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from open_webui.models import declaracion_borradores as modelo
from open_webui.models.declaracion_borradores import (
    ConflictoVersion,
    DeclaracionBorrador,
    DeclaracionBorradorForm,
    DeclaracionBorradores,
    IdEnUso,
)
from open_webui.navegacion.borradores import (
    E_CLAVES_DESCONOCIDAS,
    E_DEMASIADO_GRANDE,
    E_NOMBRE_VACIO,
    E_PASO_RANGO,
    E_VALOR_INVALIDO,
    MAX_BYTES_DATOS,
    errores_borrador,
)
from open_webui.routers import declaracion_borradores as router_mod

ID_A = 'borrador-aaaa-0001'
ID_B = 'borrador-bbbb-0002'


def _codigos(errores):
    return {e['codigo'] for e in errores}


# --- Validación ------------------------------------------------------------


def test_borrador_parcial_valido():
    datos = {'declarante_nombre': 'Ana', 'embalses_seleccionados': ['Belesar'], 'firma_fecha': '2026-10-29'}
    assert errores_borrador('Ana', 1, datos) == []


@pytest.mark.parametrize(
    ('nombre', 'paso', 'datos', 'codigo'),
    [
        ('  ', 1, {}, E_NOMBRE_VACIO),
        ('Ana', 0, {}, E_PASO_RANGO),
        ('Ana', 99, {}, E_PASO_RANGO),
        ('Ana', 1, {'campo_inventado': 'x'}, E_CLAVES_DESCONOCIDAS),
        ('Ana', 1, {'declarante_nombre': {'anidado': True}}, E_VALOR_INVALIDO),
        ('Ana', 1, {'embalses_seleccionados': [1, 2]}, E_VALOR_INVALIDO),
    ],
)
def test_borrador_invalido(nombre, paso, datos, codigo):
    assert codigo in _codigos(errores_borrador(nombre, paso, datos))


def test_borrador_demasiado_grande():
    claves = ['declarante_nombre', 'declarante_apellido1', 'declarante_apellido2', 'embarcacion_nombre']
    datos = {c: 'x' * 2000 for c in claves}
    datos['embalses_seleccionados'] = ['y' * 2000] * 40
    assert len(str(datos)) > MAX_BYTES_DATOS
    assert E_DEMASIADO_GRANDE in _codigos(errores_borrador('Ana', 1, datos))


# --- Base de datos -----------------------------------------------------------


@pytest.fixture
def bd(tmp_path, monkeypatch):
    """SQLite en fichero (NullPool) para poder usarlo desde distintos event loops."""
    ruta = tmp_path / 'borradores.db'
    sync_engine = create_engine(f'sqlite:///{ruta}')
    DeclaracionBorrador.__table__.create(sync_engine)
    sync_engine.dispose()

    engine = create_async_engine(f'sqlite+aiosqlite:///{ruta}', poolclass=NullPool)
    sesiones = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    @asynccontextmanager
    async def contexto(db=None):
        async with sesiones() as session:
            yield session

    monkeypatch.setattr(modelo, 'get_async_db_context', contexto)
    yield
    asyncio.run(engine.dispose())


def _form(nombre='Ana', paso=1, datos=None):
    return DeclaracionBorradorForm(nombre=nombre, paso=paso, datos=datos or {'declarante_nombre': nombre})


def test_crud_y_aislamiento(bd):
    async def caso():
        creado, existente = await DeclaracionBorradores.crear(ID_A, 'u1', _form())
        assert (creado.version, existente) == (1, False)

        repetido, existente = await DeclaracionBorradores.crear(ID_A, 'u1', _form('Otra'))
        assert existente and repetido.nombre == 'Ana'

        with pytest.raises(IdEnUso):
            await DeclaracionBorradores.crear(ID_A, 'u2', _form())

        assert await DeclaracionBorradores.obtener(ID_A, 'u2') is None
        assert await DeclaracionBorradores.listar('u2') == []
        assert await DeclaracionBorradores.actualizar(ID_A, 'u2', _form('X'), 1) is None
        assert await DeclaracionBorradores.eliminar(ID_A, 'u2') is False

        actualizado = await DeclaracionBorradores.actualizar(ID_A, 'u1', _form('Ana 2', paso=3), 1)
        assert (actualizado.version, actualizado.paso, actualizado.nombre) == (2, 3, 'Ana 2')

        with pytest.raises(ConflictoVersion) as exc:
            await DeclaracionBorradores.actualizar(ID_A, 'u1', _form('Viejo'), 1)
        assert exc.value.actual.version == 2

        [resumen] = await DeclaracionBorradores.listar('u1')
        assert resumen.id == ID_A and not hasattr(resumen, 'datos')

        assert await DeclaracionBorradores.eliminar(ID_A, 'u1') is True
        assert await DeclaracionBorradores.contar('u1') == 0

    asyncio.run(caso())


def test_purga_caducados(bd):
    async def caso():
        await DeclaracionBorradores.crear(ID_A, 'u1', _form())
        await DeclaracionBorradores.crear(ID_B, 'u1', _form())
        async with modelo.get_async_db_context() as db:
            viejo = await db.get(DeclaracionBorrador, ID_A)
            viejo.updated_at = time.time_ns() - 91 * 86_400 * 1_000_000_000
            await db.commit()

        assert await DeclaracionBorradores.purgar_caducados(0) == 0
        assert await DeclaracionBorradores.purgar_caducados(90) == 1
        assert [b.id for b in await DeclaracionBorradores.listar('u1')] == [ID_B]

    asyncio.run(caso())


# --- API ---------------------------------------------------------------------


@pytest.fixture
def cliente(bd, monkeypatch):
    app = FastAPI()
    app.include_router(router_mod.router, prefix='/borradores')
    usuario = {'id': 'u1'}
    app.dependency_overrides[router_mod.require_declaracion] = lambda: SimpleNamespace(id=usuario['id'])
    monkeypatch.setattr(router_mod, 'DECLARACION_BORRADORES_MAX', 2)
    monkeypatch.setattr(router_mod, '_ultima_purga', time.monotonic())
    with TestClient(app) as client:
        client.usuario = usuario
        yield client


def _body(id=ID_A, nombre='Ana', paso=1, **extra):
    return {'id': id, 'nombre': nombre, 'paso': paso, 'datos': {'declarante_nombre': nombre}, **extra}


def test_api_flujo_completo(cliente):
    r = cliente.post('/borradores/', json=_body())
    assert r.status_code == 200 and r.json()['version'] == 1 and r.json()['existente'] is False

    r = cliente.post('/borradores/', json=_body(nombre='Reintento'))
    assert r.json()['existente'] is True and r.json()['nombre'] == 'Ana'

    r = cliente.put(f'/borradores/{ID_A}', json={'nombre': 'Ana', 'paso': 2, 'datos': {}, 'version': 1})
    assert r.status_code == 200 and r.json()['version'] == 2

    r = cliente.put(f'/borradores/{ID_A}', json={'nombre': 'Ana', 'paso': 2, 'datos': {}, 'version': 1})
    assert r.status_code == 409
    assert r.json()['detail']['codigo'] == 'CONFLICTO_VERSION'
    assert r.json()['detail']['actual']['version'] == 2

    assert cliente.get(f'/borradores/{ID_A}').json()['paso'] == 2
    assert [b['id'] for b in cliente.get('/borradores/').json()] == [ID_A]

    assert cliente.delete(f'/borradores/{ID_A}').json() == {'eliminado': True}
    assert cliente.delete(f'/borradores/{ID_A}').json() == {'eliminado': False}
    assert cliente.get(f'/borradores/{ID_A}').status_code == 404


def test_api_validacion_y_limite(cliente):
    r = cliente.post('/borradores/', json={**_body(), 'datos': {'campo_inventado': 1}})
    assert r.status_code == 422
    assert r.json()['detail']['errores'][0]['codigo'] == E_CLAVES_DESCONOCIDAS

    assert cliente.post('/borradores/', json=_body(ID_A)).status_code == 200
    assert cliente.post('/borradores/', json=_body(ID_B)).status_code == 200
    r = cliente.post('/borradores/', json=_body('borrador-cccc-0003'))
    assert r.status_code == 422 and r.json()['detail']['codigo'] == 'MAX_BORRADORES'
    # Reintentar uno existente no cuenta contra el límite.
    assert cliente.post('/borradores/', json=_body(ID_A)).status_code == 200


def test_api_aislamiento_entre_usuarios(cliente):
    cliente.post('/borradores/', json=_body())
    cliente.usuario['id'] = 'u2'
    assert cliente.get('/borradores/').json() == []
    assert cliente.get(f'/borradores/{ID_A}').status_code == 404
    r = cliente.put(f'/borradores/{ID_A}', json={'nombre': 'X', 'paso': 1, 'datos': {}, 'version': 1})
    assert r.status_code == 404
    assert cliente.delete(f'/borradores/{ID_A}').json() == {'eliminado': False}
    assert cliente.post('/borradores/', json=_body()).status_code == 409
