import sys
from pathlib import Path

# ============================================================
# Make AI/src importable
# ============================================================

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from recommendations.decision_engine import compute_overall_risk
import recommendations.diagnosis as diagnosis_module


# ============================================================
# Fake weather functions
# ============================================================

def fake_good_weather(latitude, longitude, redis_instance=None):
    """
    Simulates normal weather.
    No precipitation and no severe weather condition.
    """
    return {
        "temperature": 25.0,
        "precipitation": 0.0,
        "humidity": 50,
        "wind_speed": 10,
        "wind_direction": 180,
        "pressure": 1015,
        "weather_condition": "clear",
        "timestamp": "2026-08-25T12:00",
    }


def fake_bad_weather(latitude, longitude, redis_instance=None):
    """
    Simulates bad weather.
    Significant precipitation + heavy rain.
    """
    return {
        "temperature": 18.0,
        "precipitation": 5.2,
        "humidity": 90,
        "wind_speed": 30,
        "wind_direction": 180,
        "pressure": 1000,
        "weather_condition": "heavy_rain",
        "timestamp": "2026-08-25T12:00",
    }


# ============================================================
# Test helper
# ============================================================

def run_test(test_name, row, weather_function):
    """
    Execute one Phase 8 test with controlled weather data.
    """

    original_weather_function = diagnosis_module.get_weather_cached

    try:
        # Replace real API call by controlled test weather
        diagnosis_module.get_weather_cached = weather_function

        result = compute_overall_risk(row)

        print("\n" + "=" * 80)
        print(test_name)
        print("=" * 80)

        print(f"RSL DIFF       : {row['RSL DIFF']} dB")
        print(f"Fade margin    : {row['min_fade_margin']} dB")
        print(f"Sanity         : {row['Sanity']}")
        print(f"FH Status      : {row['Status']}")
        print(f"Risk level     : {result['risk_level']}")
        print(f"Risk points    : {result['risk_points']}")

        print("\nRAISONS:")
        print(result["raisons"])

        print("\nCAUSES POSSIBLES:")
        print(result["causes_possibles"])

        return result

    finally:
        # Restore the real weather function
        diagnosis_module.get_weather_cached = original_weather_function


# ============================================================
# Common coordinates
# ============================================================

coordinates = {
    "EndA_Latitude": 36.8065,
    "EndA_Longitude": 10.1815,
}


# ============================================================
# TEST 1
# LOW + normal weather + comfortable fade margin
# ============================================================

test1 = {
    "RSL DIFF": 3.0,
    "Sanity": "OK",
    "Status": "Lien_OK",
    "min_fade_margin": 30.0,
    **coordinates,
}

result1 = run_test(
    "TEST 1 — LOW + météo normale + marge confortable",
    test1,
    fake_good_weather,
)


# ============================================================
# TEST 2
# LOW + bad weather + low fade margin
# ============================================================

test2 = {
    "RSL DIFF": 3.0,
    "Sanity": "OK",
    "Status": "Lien_OK",
    "min_fade_margin": 10.0,
    **coordinates,
}

result2 = run_test(
    "TEST 2 — LOW + mauvaise météo + faible marge",
    test2,
    fake_bad_weather,
)


# ============================================================
# TEST 3
# MEDIUM + normal weather + comfortable fade margin
# ============================================================

test3 = {
    "RSL DIFF": 7.0,
    "Sanity": "PREVENTIVE",
    "Status": "Lien_dépointé_(<10)",
    "min_fade_margin": 30.0,
    **coordinates,
}

result3 = run_test(
    "TEST 3 — MEDIUM + météo normale + marge confortable",
    test3,
    fake_good_weather,
)


# ============================================================
# TEST 4
# MEDIUM + bad weather + low fade margin
# ============================================================

test4 = {
    "RSL DIFF": 7.0,
    "Sanity": "PREVENTIVE",
    "Status": "Lien_dépointé_(<10)",
    "min_fade_margin": 10.0,
    **coordinates,
}

result4 = run_test(
    "TEST 4 — MEDIUM + mauvaise météo + faible marge",
    test4,
    fake_bad_weather,
)


# ============================================================
# TEST 5
# HIGH + normal weather + comfortable fade margin
# ============================================================

test5 = {
    "RSL DIFF": 12.0,
    "Sanity": "CURATIVE",
    "Status": "Lien_dépointé_(>10)",
    "min_fade_margin": 30.0,
    **coordinates,
}

result5 = run_test(
    "TEST 5 — HIGH + météo normale + marge confortable",
    test5,
    fake_good_weather,
)


# ============================================================
# TEST 6
# HIGH + bad weather + low fade margin
# ============================================================

test6 = {
    "RSL DIFF": 12.0,
    "Sanity": "CURATIVE",
    "Status": "Lien_dépointé_(>10)",
    "min_fade_margin": 10.0,
    **coordinates,
}

result6 = run_test(
    "TEST 6 — HIGH + mauvaise météo + faible marge",
    test6,
    fake_bad_weather,
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\n")
print("=" * 80)
print("PHASE 8 — VALIDATION FINALE")
print("=" * 80)

expected_results = [
    ("Test 1", result1, "LOW"),
    ("Test 2", result2, "LOW"),
    ("Test 3", result3, "MEDIUM"),
    ("Test 4", result4, "MEDIUM"),
    ("Test 5", result5, "HIGH"),
    ("Test 6", result6, "HIGH"),
]

all_passed = True

for test_name, result, expected in expected_results:

    actual = result["risk_level"]

    if actual == expected:
        print(f"✓ {test_name}: PASS — {actual}")
    else:
        print(
            f"✗ {test_name}: FAIL — "
            f"attendu = {expected}, obtenu = {actual}"
        )
        all_passed = False


print("\n" + "=" * 80)

if all_passed:
    print("✓ PHASE 8 COMPLETE — LES 6 TESTS SONT PASSÉS")
else:
    print("✗ PHASE 8 FAILED — IL FAUT CORRIGER LES TESTS")

print("=" * 80)