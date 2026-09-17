import pandas as pd
from weather.weather_service import get_weather_cached


def build_diagnosis(row: dict) -> dict:
    """
    Build French, evidence-gated diagnostic reasons and possible causes.
    Does NOT touch risk_level — that comes only from compute_risk_severity().
    Every reason is only added if real, non-null data supports it.
    """
    raisons = []
    causes_possibles = []

    rsl_diff = row.get("RSL DIFF")

    # --- RSL DIFF description (always present if we have a value) ---
    if rsl_diff is not None and pd.notna(rsl_diff):
        abs_diff = abs(rsl_diff)
        if abs_diff < 5:
            raisons.append(
                f"Écart RSL de {abs_diff:.2f} dB par rapport à la référence : "
                f"aucune dégradation importante détectée selon le critère RSL."
            )
        elif abs_diff < 10:
            raisons.append(
                f"Dépointage modéré du lien : écart RSL de {abs_diff:.2f} dB par rapport à la référence."
            )
            causes_possibles.append("Léger désalignement d'antenne possible")
        else:
            raisons.append(
                f"Dépointage important du lien : écart RSL de {abs_diff:.2f} dB par rapport à la référence."
            )
            causes_possibles.append("Désalignement d'antenne probable")

    # --- Sanity: only as supporting technical evidence, never overriding severity ---
    sanity = row.get("Sanity")
    if sanity == "CURATIVE":
        raisons.append(
            "Les indicateurs de performance et d'erreurs associés au lien sont compatibles "
            "avec un état nécessitant une intervention corrective."
        )
        causes_possibles.append("Problèmes techniques nécessitant une intervention")
    elif sanity == "PREVENTIVE":
        raisons.append(
            "Les indicateurs de performance associés au lien suggèrent une maintenance préventive."
        )

    # --- Fade margin: only if we have a real, non-null value ---
    fade_margin = row.get("min_fade_margin")
    if fade_margin is not None and pd.notna(fade_margin):
        if fade_margin < 15:
            raisons.append(
                f"Marge de fading faible ({fade_margin:.2f} dB), offrant une protection limitée "
                f"contre les variations de propagation."
            )
            causes_possibles.append("Sensibilité accrue au fading")
        else:
            raisons.append(
                f"Marge de fading confortable ({fade_margin:.2f} dB)."
            )

    # --- RTWP: only if we have real anomaly data for this site ---
    rtwp_anomaly_count = row.get("rtwp_anomaly_count")
    rtwp_max_imbalance = row.get("rtwp_max_imbalance")

    if rtwp_anomaly_count is not None and pd.notna(rtwp_anomaly_count) and rtwp_anomaly_count > 0:
        if rtwp_max_imbalance is not None and pd.notna(rtwp_max_imbalance) and rtwp_max_imbalance >= 5:
            raisons.append(
                f"Indicateurs RTWP anormaux détectés sur le site, avec un déséquilibre "
                f"entre chaînes d'antenne de {rtwp_max_imbalance:.2f} dB, pouvant indiquer "
                f"une interférence radio ou un problème d'équilibrage d'antenne."
            )
            causes_possibles.append("Déséquilibre d'antenne ou interférence radio (déséquilibre mesuré)")
        else:
            raisons.append(
                f"Indicateurs RTWP anormaux détectés sur le site "
                f"({int(rtwp_anomaly_count)} anomalie(s)), sans déséquilibre d'antenne significatif mesuré."
            )
            causes_possibles.append("Interférence radio possible (à valider)")

    # --- Weather: contextual only, never affects risk_level, never claims causality ---
    # (independent of RTWP — must NOT be nested inside the RTWP block above)
    latitude = row.get("EndA_Latitude")
    longitude = row.get("EndA_Longitude")
    redis_instance = row.get("_redis_instance")  # optional, passed in by the caller
    prefetched_weather = row.get("_weather")  # optional, avoids a live call during bulk processing

    weather = prefetched_weather
    if weather is None and latitude is not None and pd.notna(latitude) and longitude is not None and pd.notna(longitude):
        weather = get_weather_cached(latitude, longitude, redis_instance=redis_instance)

    if weather is not None:
        precipitation = weather.get("precipitation")
        condition = weather.get("weather_condition")

        is_bad_weather = (
            (precipitation is not None and precipitation > 1.0)
            or condition in ("rain", "heavy_rain", "rain_showers", "violent_rain_showers", "thunderstorm")
        )

        if is_bad_weather:
            if fade_margin is not None and pd.notna(fade_margin) and fade_margin < 15:
                raisons.append(
                    f"Faible marge de fading ({fade_margin:.2f} dB) et précipitations "
                    f"observées dans la zone du site ({precipitation} mm), ce qui peut rendre "
                    f"le lien plus sensible aux variations de propagation."
                )
                causes_possibles.append(
                    "Conditions météorologiques potentiellement défavorables, combinées à une marge de fading limitée"
                )
            else:
                raisons.append(
                    f"Des précipitations sont observées dans la zone du site ({precipitation} mm), "
                    f"mais la marge de fading reste"
                    + (f" confortable ({fade_margin:.2f} dB)." if fade_margin is not None and pd.notna(fade_margin) else " non déterminée.")
                )

    # --- Disagreement flag between Sanity and FH RSL status, kept as neutral info ---
    status = row.get("Status")
    if sanity is not None and status is not None:
        sanity_bad = sanity in ("CURATIVE", "PREVENTIVE")
        fh_bad = status != "Lien_OK"
        if sanity_bad != fh_bad:
            raisons.append(
                "Les classificateurs Sanity et FH RSL ne sont pas en accord sur l'état de ce lien ; "
                "une vérification manuelle est recommandée."
            )

    if not raisons:
        raisons.append("Aucun indicateur de risque détecté.")

    return {
        "raisons": raisons,
        "causes_possibles": causes_possibles,
    }