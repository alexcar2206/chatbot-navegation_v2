"""Dependencias FastAPI compartidas por los routers de mapa y declaración."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, status

from open_webui.constants import ERROR_MESSAGES
from open_webui.models.config import Config
from open_webui.utils.access_control import has_permission
from open_webui.utils.auth import get_admin_user, get_verified_user


def require_feature(
    config_key: str,
    permission_key: str,
    *,
    admin: bool = False,
    disabled_detail: str = 'Funcionalidad deshabilitada',
) -> Callable[..., Awaitable]:
    """Exige el flag global ``config_key`` y, para no admins, el permiso ``permission_key``.

    Sigue el mismo patrón que ``features.notes`` (routers/notes.py).
    """
    base_dependency = get_admin_user if admin else get_verified_user

    async def dependency(user=Depends(base_dependency)):
        if await Config.get(config_key) is False:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=disabled_detail)
        if user.role != 'admin' and not await has_permission(
            user.id, permission_key, await Config.get('user.permissions')
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ERROR_MESSAGES.UNAUTHORIZED)
        return user

    return dependency
