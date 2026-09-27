#!/usr/bin/env python3
"""
CivicPulse Seed Script
Populates the database with 30 realistic, deterministic complaints across all categories,
priorities, and statuses.

Idempotency: Uses fixed UUIDs and ON CONFLICT (id) DO NOTHING.
Running multiple times is completely safe.
"""

import asyncio
import sys
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Seed dataset: Exactly 30 complaints (5 per category)
SEED_COMPLAINTS = [
    # WATER (5)
    {
        "id": "11111111-1111-4000-8000-000000000001",
        "text": "Main water pipeline burst near Street 12, water flooding houses.",
        "location": "Sector F-7/2, Street 12",
        "reporter_contact": "citizen1@example.com",
        "category": "water",
        "priority": "high",
        "status": "open",
        "ai_summary": "Burst pipeline flooding residential street.",
        "triaged_by": "simulated",
        "triage_latency_ms": 45,
    },
    {
        "id": "11111111-1111-4000-8000-000000000002",
        "text": "Low water pressure in municipal supply line for the past 3 days.",
        "location": "Gulshan-e-Iqbal Block 4",
        "reporter_contact": "+923001112233",
        "category": "water",
        "priority": "normal",
        "status": "in_progress",
        "ai_summary": "Low supply pressure over multiple days.",
        "triaged_by": "simulated",
        "triage_latency_ms": 52,
    },
    {
        "id": "11111111-1111-4000-8000-000000000003",
        "text": "Contaminated yellowish drinking water coming from main valve.",
        "location": "DHA Phase 5, Sector B",
        "reporter_contact": None,
        "category": "water",
        "priority": "high",
        "status": "open",
        "ai_summary": "Contaminated municipal drinking water.",
        "triaged_by": "simulated",
        "triage_latency_ms": 38,
    },
    {
        "id": "11111111-1111-4000-8000-000000000004",
        "text": "Public water filtration plant tap is leaking continuously.",
        "location": "G-9 Community Park Gate 1",
        "reporter_contact": "park_volunteer@city.org",
        "category": "water",
        "priority": "low",
        "status": "resolved",
        "ai_summary": "Leaking tap at public water plant.",
        "triaged_by": "simulated",
        "triage_latency_ms": 30,
    },
    {
        "id": "11111111-1111-4000-8000-000000000005",
        "text": "Request to install swimming pool drainage connection.",
        "location": "Private Villa 44, Bahria Enclave",
        "reporter_contact": "+923009988776",
        "category": "water",
        "priority": "low",
        "status": "rejected",
        "ai_summary": "Private property drainage request out of municipal scope.",
        "triaged_by": "simulated",
        "triage_latency_ms": 61,
    },

    # ELECTRICITY (5)
    {
        "id": "22222222-2222-4000-8000-000000000001",
        "text": "High-voltage transformer sparking dangerously above busy marketplace.",
        "location": "Commercial Market, Block D",
        "reporter_contact": "shop_association@mail.com",
        "category": "electricity",
        "priority": "high",
        "status": "open",
        "ai_summary": "Hazardous sparking transformer over commercial zone.",
        "triaged_by": "simulated",
        "triage_latency_ms": 42,
    },
    {
        "id": "22222222-2222-4000-8000-000000000002",
        "text": "Dangling electric wire hanging low across pedestrian sidewalk.",
        "location": "School Road, near City Grammar School",
        "reporter_contact": "+923214455667",
        "category": "electricity",
        "priority": "high",
        "status": "in_progress",
        "ai_summary": "Low hanging power cable near school zone.",
        "triaged_by": "simulated",
        "triage_latency_ms": 47,
    },
    {
        "id": "22222222-2222-4000-8000-000000000003",
        "text": "Frequent unannounced voltage fluctuations damaging home appliances.",
        "location": "Model Town Block J",
        "reporter_contact": "resident_j@gmail.com",
        "category": "electricity",
        "priority": "normal",
        "status": "open",
        "ai_summary": "Severe voltage fluctuation in residential area.",
        "triaged_by": "simulated",
        "triage_latency_ms": 35,
    },
    {
        "id": "22222222-2222-4000-8000-000000000004",
        "text": "Substation feeder trip fixed after storm yesterday.",
        "location": "Industrial Area Sector I-9",
        "reporter_contact": "factory4@ind.pk",
        "category": "electricity",
        "priority": "normal",
        "status": "resolved",
        "ai_summary": "Feeder restoration after weather disruption.",
        "triaged_by": "simulated",
        "triage_latency_ms": 29,
    },
    {
        "id": "22222222-2222-4000-8000-000000000005",
        "text": "Complaint regarding private solar net metering tariff dispute.",
        "location": "Canal View House 112",
        "reporter_contact": "+923335551122",
        "category": "electricity",
        "priority": "low",
        "status": "rejected",
        "ai_summary": "Billing tariff dispute handled by regulatory authority.",
        "triaged_by": "simulated",
        "triage_latency_ms": 50,
    },

    # SANITATION (5)
    {
        "id": "33333333-3333-4000-8000-000000000001",
        "text": "Open sewer overflowing directly onto main hospital entrance road.",
        "location": "Civil Hospital Gate 2 Road",
        "reporter_contact": "hospital_admin@health.gov",
        "category": "sanitation",
        "priority": "high",
        "status": "open",
        "ai_summary": "Overflowing sewer blocking hospital entrance.",
        "triaged_by": "simulated",
        "triage_latency_ms": 39,
    },
    {
        "id": "33333333-3333-4000-8000-000000000002",
        "text": "Garbage dump not collected for one week, foul odor spreading.",
        "location": "Sector G-8/1 Street 4",
        "reporter_contact": "+923456677889",
        "category": "sanitation",
        "priority": "normal",
        "status": "in_progress",
        "ai_summary": "Uncollected municipal waste pile.",
        "triaged_by": "simulated",
        "triage_latency_ms": 44,
    },
    {
        "id": "33333333-3333-4000-8000-000000000003",
        "text": "Dead animal carcass on green belt near central roundabout.",
        "location": "Kashmir Highway Chowk",
        "reporter_contact": None,
        "category": "sanitation",
        "priority": "high",
        "status": "open",
        "ai_summary": "Animal carcass on major transit green belt.",
        "triaged_by": "simulated",
        "triage_latency_ms": 36,
    },
    {
        "id": "33333333-3333-4000-8000-000000000004",
        "text": "Public park trash cans emptied and sanitized.",
        "location": "Fatima Jinnah Park Sector F-9",
        "reporter_contact": "parks_dept@cda.gov",
        "category": "sanitation",
        "priority": "low",
        "status": "resolved",
        "ai_summary": "Scheduled cleaning completed.",
        "triaged_by": "simulated",
        "triage_latency_ms": 31,
    },
    {
        "id": "33333333-3333-4000-8000-000000000005",
        "text": "Request to clean private backyard garden waste.",
        "location": "House 18, Street 90, G-11/3",
        "reporter_contact": "+923001234567",
        "category": "sanitation",
        "priority": "low",
        "status": "rejected",
        "ai_summary": "Private garden waste disposal out of scope.",
        "triaged_by": "simulated",
        "triage_latency_ms": 48,
    },

    # ROADS (5)
    {
        "id": "44444444-4444-4000-8000-000000000001",
        "text": "Massive sinkhole opened up in the middle of two-lane avenue.",
        "location": "Jinnah Avenue near Blue Area",
        "reporter_contact": "traffic_warden_12@police.gov",
        "category": "roads",
        "priority": "high",
        "status": "open",
        "ai_summary": "Dangerous sinkhole on major avenue causing road hazard.",
        "triaged_by": "simulated",
        "triage_latency_ms": 40,
    },
    {
        "id": "44444444-4444-4000-8000-000000000002",
        "text": "Deep potholes causing severe vehicular damage near flyover ramp.",
        "location": "Murree Road Rehmanabad Flyover",
        "reporter_contact": "+923129876543",
        "category": "roads",
        "priority": "normal",
        "status": "in_progress",
        "ai_summary": "Road surface degradation and severe potholes.",
        "triaged_by": "simulated",
        "triage_latency_ms": 41,
    },
    {
        "id": "44444444-4444-4000-8000-000000000003",
        "text": "Missing storm drain manhole cover creating fatal hazard for bikes.",
        "location": "College Road, Sector H-8",
        "reporter_contact": "student_union@college.edu",
        "category": "roads",
        "priority": "high",
        "status": "open",
        "ai_summary": "Uncovered manhole on main roadway.",
        "triaged_by": "simulated",
        "triage_latency_ms": 37,
    },
    {
        "id": "44444444-4444-4000-8000-000000000004",
        "text": "Speed breaker repainting completed with reflective markers.",
        "location": "Service Road North, Sector I-10",
        "reporter_contact": "traffic_dept@city.gov",
        "category": "roads",
        "priority": "low",
        "status": "resolved",
        "ai_summary": "Speed breaker marking maintenance completed.",
        "triaged_by": "simulated",
        "triage_latency_ms": 28,
    },
    {
        "id": "44444444-4444-4000-8000-000000000005",
        "text": "Request to pave private residential driveway inside boundary wall.",
        "location": "Plot 55, Park View City",
        "reporter_contact": "+923005544332",
        "category": "roads",
        "priority": "low",
        "status": "rejected",
        "ai_summary": "Private interior paving request rejected.",
        "triaged_by": "simulated",
        "triage_latency_ms": 53,
    },

    # STREETLIGHTS (5)
    {
        "id": "55555555-5555-4000-8000-000000000001",
        "text": "Entire sector main boulevard streetlights pitch dark for 4 nights.",
        "location": "7th Avenue from Khayaban to Islamabad Club",
        "reporter_contact": "citizens_watch@community.org",
        "category": "streetlights",
        "priority": "high",
        "status": "open",
        "ai_summary": "Major arterial roadway completely dark.",
        "triaged_by": "simulated",
        "triage_latency_ms": 46,
    },
    {
        "id": "55555555-5555-4000-8000-000000000002",
        "text": "Streetlight pole bent and leaning dangerously over parked cars.",
        "location": "Street 38, Sector F-10/1",
        "reporter_contact": "+923334445556",
        "category": "streetlights",
        "priority": "normal",
        "status": "in_progress",
        "ai_summary": "Structurally damaged pole leaning over vehicles.",
        "triaged_by": "simulated",
        "triage_latency_ms": 43,
    },
    {
        "id": "55555555-5555-4000-8000-000000000003",
        "text": "Flickering LED streetlight pole #14 making buzzing loud noise.",
        "location": "Street 5, Sector E-11/2",
        "reporter_contact": None,
        "category": "streetlights",
        "priority": "low",
        "status": "open",
        "ai_summary": "Flickering luminaire with acoustic disturbance.",
        "triaged_by": "simulated",
        "triage_latency_ms": 33,
    },
    {
        "id": "55555555-5555-4000-8000-000000000004",
        "text": "Replaced faulty sodium bulb with 120W LED fixture.",
        "location": "Main Market Sector I-8/2",
        "reporter_contact": "electrical_maint@city.gov",
        "category": "streetlights",
        "priority": "normal",
        "status": "resolved",
        "ai_summary": "Routine streetlight bulb replacement.",
        "triaged_by": "simulated",
        "triage_latency_ms": 30,
    },
    {
        "id": "55555555-5555-4000-8000-000000000005",
        "text": "Request to install decorative floodlights for private wedding event.",
        "location": "House 100, Sector F-6/3",
        "reporter_contact": "+923008889900",
        "category": "streetlights",
        "priority": "low",
        "status": "rejected",
        "ai_summary": "Private event illumination request rejected.",
        "triaged_by": "simulated",
        "triage_latency_ms": 55,
    },

    # OTHER (5)
    {
        "id": "66666666-6666-4000-8000-000000000001",
        "text": "Large ancient eucalyptus tree branch fallen blocking entrance to clinic.",
        "location": "Sector G-6/2, Post Office Road",
        "reporter_contact": "clinic_manager@health.pk",
        "category": "other",
        "priority": "high",
        "status": "open",
        "ai_summary": "Fallen tree branch obstructing medical clinic.",
        "triaged_by": "simulated",
        "triage_latency_ms": 44,
    },
    {
        "id": "66666666-6666-4000-8000-000000000002",
        "text": "Illegal advertising billboard erected without permit blocking view.",
        "location": "Peshawar Mor Intersection",
        "reporter_contact": "+923215566778",
        "category": "other",
        "priority": "normal",
        "status": "in_progress",
        "ai_summary": "Unpermitted commercial billboard obstruction.",
        "triaged_by": "simulated",
        "triage_latency_ms": 49,
    },
    {
        "id": "66666666-6666-4000-8000-000000000003",
        "text": "Excessive construction noise violating municipal decibel rules past 2 AM.",
        "location": "Sector F-11/4, Plot 92",
        "reporter_contact": "night_resident@mail.com",
        "category": "other",
        "priority": "normal",
        "status": "open",
        "ai_summary": "Nighttime noise ordinance violation.",
        "triaged_by": "simulated",
        "triage_latency_ms": 37,
    },
    {
        "id": "66666666-6666-4000-8000-000000000004",
        "text": "Stray dog vaccination and tagging drive completed.",
        "location": "Sector H-9 Green Belt",
        "reporter_contact": "animal_welfare@city.gov",
        "category": "other",
        "priority": "low",
        "status": "resolved",
        "ai_summary": "Animal control vaccination campaign completed.",
        "triaged_by": "simulated",
        "triage_latency_ms": 32,
    },
    {
        "id": "66666666-6666-4000-8000-000000000005",
        "text": "Civil dispute between neighbors regarding tree leaf shedding.",
        "location": "Sector I-8/4, Street 19",
        "reporter_contact": "+923007778899",
        "category": "other",
        "priority": "low",
        "status": "rejected",
        "ai_summary": "Private neighbor dispute non-actionable by municipality.",
        "triaged_by": "simulated",
        "triage_latency_ms": 58,
    },
]


async def seed_database():
    from app.config import get_settings
    settings = get_settings()

    print(f"🌱 Seeding database at {settings.DATABASE_URL}...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    insert_sql = text("""
        INSERT INTO complaints (
            id, text, location, reporter_contact,
            category, priority, status, ai_summary,
            triaged_by, triage_latency_ms, created_at, updated_at
        ) VALUES (
            :id, :text, :location, :reporter_contact,
            :category, :priority, :status, :ai_summary,
            :triaged_by, :triage_latency_ms, NOW(), NOW()
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    async with engine.begin() as conn:
        inserted = 0
        for item in SEED_COMPLAINTS:
            res = await conn.execute(insert_sql, item)
            inserted += res.rowcount

    await engine.dispose()
    print(f"✅ Seeding complete! Inserted {inserted} new complaint(s) (Total seed records: {len(SEED_COMPLAINTS)}).")


if __name__ == "__main__":
    asyncio.run(seed_database())
