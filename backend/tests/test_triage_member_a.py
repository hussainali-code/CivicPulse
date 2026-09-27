import pytest

from app.models import Category, Priority
from app.providers.triage.factory import get_triage_provider
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage


@pytest.mark.asyncio
async def test_rule_based_triage_categories():
    triage = RuleBasedTriage()

    # Water
    res_water = await triage.triage("Main water pipeline burst near Street 12, water flooding houses.", "Sector F-7")
    assert res_water.category == Category.WATER
    assert res_water.priority == Priority.HIGH

    # Electricity
    res_elec = await triage.triage("High voltage transformer sparking dangerously above busy market.", "Commercial Block")
    assert res_elec.category == Category.ELECTRICITY
    assert res_elec.priority == Priority.HIGH

    # Sanitation
    res_san = await triage.triage("Open sewer overflowing and garbage dump not collected.", "Sector G-8")
    assert res_san.category == Category.SANITATION

    # Roads
    res_road = await triage.triage("Massive sinkhole opened up in the middle of avenue.", "Jinnah Avenue")
    assert res_road.category == Category.ROADS
    assert res_road.priority == Priority.HIGH

    # Streetlights
    res_light = await triage.triage("Streetlight pole bent and entire road pitch dark.", "Street 5")
    assert res_light.category == Category.STREETLIGHTS

    # Other fallback
    res_other = await triage.triage("Random unclassified citizen inquiry.", "Unknown")
    assert res_other.category == Category.OTHER


@pytest.mark.asyncio
async def test_simulated_triage_determinism():
    triage = SimulatedTriage()
    text = "Main water pipeline burst near Street 12"
    location = "Sector F-7"

    res1 = await triage.triage(text, location)
    res2 = await triage.triage(text, location)

    assert res1.category == res2.category
    assert res1.priority == res2.priority
    assert res1.confidence == res2.confidence
    assert res1.summary == res2.summary


@pytest.mark.asyncio
async def test_simulated_triage_fault_injections():
    # Failure injection
    triage_fail = SimulatedTriage(failure_injection=True)
    with pytest.raises(RuntimeError) as exc_fail:
        await triage_fail.triage("Broken pipe", "Loc")
    assert "Simulated triage failure injection triggered" in str(exc_fail.value)

    # Malformed injection
    triage_mal = SimulatedTriage(malformed_injection=True)
    with pytest.raises(ValueError) as exc_mal:
        await triage_mal.triage("Broken pipe", "Loc")
    assert "Simulated malformed output injection triggered" in str(exc_mal.value)


def test_triage_factory():
    rules_provider = get_triage_provider("rules")
    assert isinstance(rules_provider, RuleBasedTriage)
    assert rules_provider.name == "rules"

    sim_provider = get_triage_provider("simulated")
    assert isinstance(sim_provider, SimulatedTriage)
    assert sim_provider.name == "simulated"

    fallback_provider = get_triage_provider("unknown_nonexistent_provider")
    assert isinstance(fallback_provider, SimulatedTriage)
