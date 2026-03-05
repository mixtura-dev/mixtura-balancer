import logging

from faststream import Depends, ExceptionMiddleware, FastStream
from faststream.rabbit import Channel, RabbitBroker, RabbitRouter

from balancer_service.env_config import env

from ..domain.balance_engine import AsyncBalanceEngine, get_async_engine
from ..domain.models.balance import DraftBalances
from ..domain.models.balance_request import BalanceRequest
from ..logging_setup import setup_logging
from .exceptions import DomainException
from .schemas import ErrorResponse, ResponseMessage

exc_middleware = ExceptionMiddleware()
logger = logging.getLogger(__name__)


@exc_middleware.add_handler(DomainException, publish=True)
async def error_handler(exc: DomainException) -> ResponseMessage[ErrorResponse]:
    return ResponseMessage(status=exc.status_code, message=ErrorResponse(message=exc.message))


broker = RabbitBroker(
    env.rabbit.url,
    middlewares=[exc_middleware],
    default_channel=Channel(prefetch_count=10),
)

router = RabbitRouter()

router.subscriber("mix_balance_service.balance")


async def balance_handler(
    message: BalanceRequest, balance_engine: AsyncBalanceEngine = Depends(get_async_engine)
) -> ResponseMessage[DraftBalances]:
    logger.info(
        f"Received balance request for draft_id={message.draft_id} with {len(message.players)} players"
    )
    result = await balance_engine.find_balances_async(message)
    return ResponseMessage(status=200, message=result)


broker.include_router(router)

app = FastStream(broker)


@app.on_startup
async def startup():
    setup_logging()
