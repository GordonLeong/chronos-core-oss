import asyncio
import logging
from datetime import datetime, timezone
import random

from services.contracts import ExecutionAdapter, ExecutionIntent, ExecutionFill
from services.adapter_registry import register_execution_adapter

logger = logging.getLogger(__name__)

class LocalSimExecutionAdapter(ExecutionAdapter):
    """
    Simulated local broker ExecutionAdapter stub.
    Accepts intents, waits briefly to simulate latency, and returns fills.
    """
    
    async def submit_intent(self, intent: ExecutionIntent) -> ExecutionFill:
        logger.info(
            "Emitting simulated %s intent for %s: %s @ %s", 
            intent.action, intent.quantity, intent.ticker, intent.order_type
        )
        
        # Simulate network latency
        await asyncio.sleep(0.5)
        
        mock_fill_price = 0.0
        if intent.limit_price is not None:
            # Assume it just executes slightly better or at requested limit
            mock_fill_price = round(intent.limit_price, 2)
        else:
            # Fallback random mock price around 100
            mock_fill_price = round(100.0 + random.uniform(-1, 1), 2)
            
        return ExecutionFill(
            intent=intent,
            filled_at=datetime.now(timezone.utc),
            filled_qty=intent.quantity,
            avg_price=mock_fill_price,
            status="filled"
        )

register_execution_adapter("local_sim", LocalSimExecutionAdapter())
