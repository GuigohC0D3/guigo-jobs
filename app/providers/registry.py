from __future__ import annotations

from app.core.config import settings
from app.providers.arbeitnow import ArbeitnowProvider
from app.providers.base import BaseProvider
from app.providers.remoteok import RemoteOKProvider
from app.providers.remotive import RemotiveProvider
from app.providers.themuse import TheMuseProvider


def get_active_providers() -> list[BaseProvider]:
    providers: list[BaseProvider] = []

    if settings.enable_remoteok:
        providers.append(RemoteOKProvider())
    if settings.enable_remotive:
        providers.append(RemotiveProvider())
    if settings.enable_arbeitnow:
        providers.append(ArbeitnowProvider())
    if settings.enable_themuse:
        providers.append(TheMuseProvider())

    return providers
