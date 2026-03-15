import pytest
from fastapi import HTTPException
from src.api.routes.root_agent_personas import get_personas


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "intent_name",
    [
        "flight_booking",
        "Flight Booking",
        "flight-booking",
        "Flight_Booking",
        "BookFlight",
    ],
)
async def test_get_personas_supports_intent_name_variants(intent_name: str):
    response = await get_personas(intent_name=intent_name)
    assert len(response.personas) > 0


@pytest.mark.asyncio
async def test_get_personas_raises_for_unknown_intent():
    with pytest.raises(HTTPException) as exc_info:
        await get_personas(intent_name="unknown_intent")
    assert exc_info.value.status_code == 404
