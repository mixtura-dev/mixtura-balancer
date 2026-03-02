import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.schemas.requests import BalanceRequest, PaginationRequest
from app.schemas.responses import (
    BalanceResponse,
    PaginatedBalanceResponse,
    ErrorResponse,
    BalanceCreatedResponse,
    HealthResponse,
)
from app.models.player import Player
from app.models.settings import BalanceSettings, RoleSettings, MathSettings
from app.services.balance_service import BalanceService
from app.services.redis_service import RedisService
from app.api.dependencies import get_balance_service, get_redis_service
from app.exceptions import BalanceServiceException, DraftNotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["balance"])


def convert_request_to_models(request: BalanceRequest) -> tuple[list[Player], BalanceSettings]:
    """Конвертация запроса в модели"""
    players = [Player(member_id=p.member_id, roles=p.roles) for p in request.players]

    settings = BalanceSettings(
        max_in_team=request.settings.max_in_team,
        roles={
            role_id: RoleSettings(
                original_game_role=rs.original_game_role,
                max_in_team=rs.max_in_team,
                min_in_team=rs.min_in_team,
            )
            for role_id, rs in request.settings.roles.items()
        },
        math=MathSettings(
            alpha=request.settings.math.alpha,
            beta=request.settings.math.beta,
            gamma=request.settings.math.gamma,
            p=request.settings.math.p,
            q=request.settings.math.q,
        ),
        balance_limit=request.settings.balance_limit,
    )

    return players, settings


async def process_balance(
    draft_id: str, players: list[Player], settings: BalanceSettings, balance_service: BalanceService
) -> None:
    """Фоновая задача для расчёта баланса"""
    try:
        await balance_service.create_balance(draft_id, players, settings)
    except Exception as e:
        logger.error(f"Background balance calculation failed: {e}")


@router.post(
    "/balance",
    response_model=BalanceCreatedResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def create_balance(
    request: BalanceRequest,
    background_tasks: BackgroundTasks,
    balance_service: Annotated[BalanceService, Depends(get_balance_service)],
):
    """
    Создание запроса на балансировку.

    Балансировка выполняется в фоне. После завершения сервис мероприятий
    будет уведомлён.
    """
    try:
        players, settings = convert_request_to_models(request)

        # Запускаем расчёт в фоне
        background_tasks.add_task(
            process_balance, request.draft_id, players, settings, balance_service
        )

        return BalanceCreatedResponse(
            draft_id=request.draft_id,
            message="Balance calculation started",
            total_results=0,  # Пока неизвестно
        )

    except BalanceServiceException as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.exception("Unexpected error in create_balance")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/balance/sync",
    response_model=BalanceCreatedResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def create_balance_sync(
    request: BalanceRequest,
    balance_service: Annotated[BalanceService, Depends(get_balance_service)],
):
    """
    Синхронное создание баланса.

    Ожидает завершения расчёта и возвращает результат.
    """
    try:
        players, settings = convert_request_to_models(request)

        total = await balance_service.create_balance(request.draft_id, players, settings)

        return BalanceCreatedResponse(
            draft_id=request.draft_id, message="Balance calculation completed", total_results=total
        )

    except BalanceServiceException as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.exception("Unexpected error in create_balance_sync")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/balance/results",
    response_model=PaginatedBalanceResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_balance_results(
    request: PaginationRequest,
    balance_service: Annotated[BalanceService, Depends(get_balance_service)],
    redis_service: Annotated[RedisService, Depends(get_redis_service)],
):
    """
    Получение результатов балансировки с пагинацией.
    """
    try:
        # Проверяем существование драфта
        exists = await redis_service.draft_exists(request.draft)
        if not exists:
            raise DraftNotFoundException(request.draft)

        balances, total = await balance_service.get_balances(
            draft_id=request.draft, page=request.page, page_size=request.page_size
        )

        return PaginatedBalanceResponse(
            items=[BalanceResponse.from_result(b) for b in balances],
            total=total,
            page=request.page,
            page_size=request.page_size,
        )

    except DraftNotFoundException:
        raise HTTPException(status_code=404, detail=f"Draft not found: {request.draft}")
    except BalanceServiceException as e:
        raise HTTPException(status_code=e.code, detail=e.message)


@router.get(
    "/balance/{draft_id}/best",
    response_model=BalanceResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_best_balance(
    draft_id: str,
    balance_service: Annotated[BalanceService, Depends(get_balance_service)],
    redis_service: Annotated[RedisService, Depends(get_redis_service)],
):
    """Получение лучшего баланса для драфта"""
    exists = await redis_service.draft_exists(draft_id)
    if not exists:
        raise HTTPException(status_code=404, detail=f"Draft not found: {draft_id}")

    balances, _ = await balance_service.get_balances(draft_id, 0, 1)

    if not balances:
        raise HTTPException(status_code=404, detail="No balances found")

    return BalanceResponse.from_result(balances[0])


@router.get("/health", response_model=HealthResponse)
async def health_check(redis_service: Annotated[RedisService, Depends(get_redis_service)]):
    """Проверка здоровья сервиса"""
    redis_healthy = await redis_service.health_check()

    return HealthResponse(status="healthy" if redis_healthy else "degraded", redis=redis_healthy)
