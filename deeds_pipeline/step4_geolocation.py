"""
Step 4: Geolocation
Geocode street addresses and calculate cluster centers
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import httpx

from .utils import setup_logger, load_json, save_json, get_cache_key, load_from_cache, save_to_cache
from .config import STEP3_OUTPUT, STEP4_OUTPUT, ENABLE_CACHE


logger = setup_logger("step4_geolocation", "step4.log")


# --- Data models (ported from deed_geo_indexing) ---

@dataclass
class GeocodingCandidate:
    street_name: str
    latitude: float
    longitude: float
    address: str
    town: str
    query: str


@dataclass
class ValidatedStreet:
    street_name: str
    latitude: float
    longitude: float
    address: str
    town: str
    candidate_count: int


@dataclass
class ClusterResult:
    validated_streets: List[ValidatedStreet]
    invalid_streets: List[str]
    primary_town: str
    cluster_center_lat: float
    cluster_center_lon: float
    cluster_radius_miles: float
    final_address: Optional[str]
    confidence: float
    geocoding_stats: Dict


class StreetClusteringValidator:
    """Validate streets by clustering candidates and filtering by town."""

    MAX_CANDIDATES_PER_STREET = 5
    CLUSTERING_RADIUS_MILES = 3.0
    MILES_PER_DEGREE_LAT = 69.0
    MILES_PER_DEGREE_LON = 55.0

    def __init__(self):
        self.user_agent = "DeedGeocoder/1.0"
        self.endpoint = "https://nominatim.openstreetmap.org/search"
        self.timeout = 10.0

    async def validate_and_cluster(
        self,
        streets: List[str],
        county: str,
        state: str = "Massachusetts",
        town: Optional[str] = None,
    ) -> ClusterResult:
        if town:
            logger.info(f"Validating {len(streets)} streets in {town}, {county}, {state}")
        else:
            logger.info(f"Validating {len(streets)} streets in {county}, {state}")

        all_candidates = await self._geocode_all_streets(streets, county, state, town)
        logger.info(f"Found {len(all_candidates)} total candidates from {len(streets)} streets")

        if not all_candidates:
            return ClusterResult(
                validated_streets=[],
                invalid_streets=streets,
                primary_town="UNKNOWN",
                cluster_center_lat=0.0,
                cluster_center_lon=0.0,
                cluster_radius_miles=0.0,
                final_address=None,
                confidence=0.0,
                geocoding_stats={
                    "total_streets": len(streets),
                    "total_candidates": 0,
                    "streets_geocoded": 0,
                },
            )

        densest_cluster = self._find_densest_cluster(all_candidates)
        logger.info(
            f"Densest cluster: {len(densest_cluster['candidates'])} candidates "
            f"at ({densest_cluster['center_lat']:.4f}, {densest_cluster['center_lon']:.4f})"
        )

        primary_town = self._identify_primary_town(densest_cluster["candidates"])
        logger.info(f"Primary town identified: {primary_town}")

        validated_streets, invalid_streets = self._filter_by_town(
            all_candidates, streets, primary_town, densest_cluster
        )

        logger.info(
            f"Filtered: {len(validated_streets)} streets in {primary_town}, "
            f"{len(invalid_streets)} streets excluded"
        )

        if not validated_streets:
            return ClusterResult(
                validated_streets=[],
                invalid_streets=streets,
                primary_town=primary_town,
                cluster_center_lat=0.0,
                cluster_center_lon=0.0,
                cluster_radius_miles=0.0,
                final_address=None,
                confidence=0.0,
                geocoding_stats={
                    "total_streets": len(streets),
                    "total_candidates": len(all_candidates),
                    "streets_geocoded": len([s for s in streets if any(c.street_name == s for c in all_candidates)]),
                    "primary_town": primary_town,
                    "validated_streets": 0,
                },
            )

        center_lat, center_lon = self._calculate_centroid(validated_streets)
        radius = self._calculate_radius((center_lat, center_lon), validated_streets)
        final_address = await self._reverse_geocode(center_lat, center_lon)

        confidence = self._calculate_confidence(
            len(validated_streets), len(streets), radius
        )

        logger.info(
            f"Final cluster: {len(validated_streets)} streets, "
            f"radius {radius:.2f} mi, confidence {confidence:.1%}"
        )

        return ClusterResult(
            validated_streets=validated_streets,
            invalid_streets=invalid_streets,
            primary_town=primary_town,
            cluster_center_lat=center_lat,
            cluster_center_lon=center_lon,
            cluster_radius_miles=radius,
            final_address=final_address,
            confidence=confidence,
            geocoding_stats={
                "total_streets": len(streets),
                "total_candidates": len(all_candidates),
                "streets_geocoded": len(set(c.street_name for c in all_candidates)),
                "primary_town": primary_town,
                "validated_streets": len(validated_streets),
                "invalid_streets": len(invalid_streets),
                "cluster_radius_miles": radius,
            },
        )

    async def _geocode_all_streets(
        self, streets: List[str], county: str, state: str, town: Optional[str] = None
    ) -> List[GeocodingCandidate]:
        all_candidates: List[GeocodingCandidate] = []
        async with httpx.AsyncClient(headers={"User-Agent": self.user_agent}, timeout=self.timeout) as client:
            for street in streets:
                candidates = await self._geocode_street(client, street, county, state, town)
                all_candidates.extend(candidates)
        return all_candidates

    async def _geocode_street(
        self, client: httpx.AsyncClient, street: str, county: str, state: str, town: Optional[str] = None
    ) -> List[GeocodingCandidate]:
        candidates: List[GeocodingCandidate] = []

        street_variants = [street]
        expanded = self._expand_abbreviations(street)
        if expanded != street:
            street_variants.append(expanded)

        for street_var in street_variants:
            query = f"{street_var}, {town}, {state}" if town else f"{street_var}, {county}, {state}"
            try:
                response = await client.get(
                    self.endpoint,
                    params={"q": query, "format": "json", "limit": self.MAX_CANDIDATES_PER_STREET},
                )
                response.raise_for_status()
                results = response.json()
                logger.debug(f"Query '{query}': {len(results)} results")

                for result in results:
                    extracted_town = self._extract_town(result.get("display_name", ""))
                    candidates.append(
                        GeocodingCandidate(
                            street_name=street,
                            latitude=float(result["lat"]),
                            longitude=float(result["lon"]),
                            address=result.get("display_name", ""),
                            town=extracted_town,
                            query=query,
                        )
                    )
            except Exception as e:
                logger.debug(f"Geocoding error for '{query}': {e}")

        return candidates

    def _expand_abbreviations(self, street: str) -> str:
        abbreviations = {
            r"\bRD\b": "Road",
            r"\bDR\b": "Drive",
            r"\bAVE\b": "Avenue",
            r"\bST\b": "Street",
            r"\bLN\b": "Lane",
            r"\bCT\b": "Court",
            r"\bTERR\b": "Terrace",
            r"\bTER\b": "Terrace",
            r"\bPL\b": "Place",
            r"\bBLVD\b": "Boulevard",
        }
        expanded = street
        for abbr, full in abbreviations.items():
            expanded = re.sub(abbr, full, expanded)
        return expanded

    def _extract_town(self, address: str) -> str:
        parts = [p.strip() for p in address.split(",")]
        if len(parts) >= 2:
            return parts[1]
        return "UNKNOWN"

    def _find_densest_cluster(self, candidates: List[GeocodingCandidate]) -> Dict:
        if not candidates:
            return {"candidates": [], "center_lat": 0.0, "center_lon": 0.0}
        if len(candidates) == 1:
            return {
                "candidates": candidates,
                "center_lat": candidates[0].latitude,
                "center_lon": candidates[0].longitude,
            }

        best_cluster = None
        best_size = 0
        for seed in candidates:
            neighbors = [
                c
                for c in candidates
                if self._distance(seed.latitude, seed.longitude, c.latitude, c.longitude)
                <= self.CLUSTERING_RADIUS_MILES
            ]
            if len(neighbors) > best_size:
                best_size = len(neighbors)
                center_lat, center_lon = self._calculate_centroid(neighbors)
                best_cluster = {"candidates": neighbors, "center_lat": center_lat, "center_lon": center_lon}

        if best_cluster is None:
            center_lat, center_lon = self._calculate_centroid(candidates)
            best_cluster = {"candidates": candidates, "center_lat": center_lat, "center_lon": center_lon}
        return best_cluster

    def _identify_primary_town(self, candidates: List[GeocodingCandidate]) -> str:
        town_counts: Dict[str, int] = {}
        for c in candidates:
            town_counts[c.town] = town_counts.get(c.town, 0) + 1
        if not town_counts:
            return "UNKNOWN"
        primary_town = max(town_counts.items(), key=lambda x: x[1])[0]
        logger.info(f"Town distribution: {town_counts}")
        return primary_town

    def _filter_by_town(
        self,
        all_candidates: List[GeocodingCandidate],
        original_streets: List[str],
        primary_town: str,
        densest_cluster: Dict,
    ) -> Tuple[List[ValidatedStreet], List[str]]:
        validated_streets: List[ValidatedStreet] = []
        streets_in_validation = set()
        center = (densest_cluster["center_lat"], densest_cluster["center_lon"])

        for street in original_streets:
            street_candidates = [c for c in all_candidates if c.street_name == street]
            town_candidates = [c for c in street_candidates if c.town == primary_town]
            if not town_candidates:
                town_candidates = [
                    c for c in street_candidates if self._distance(c.latitude, c.longitude, *center) <= self.CLUSTERING_RADIUS_MILES
                ]

            if town_candidates:
                best = min(
                    town_candidates,
                    key=lambda c: self._distance(c.latitude, c.longitude, *center),
                )
                validated_streets.append(
                    ValidatedStreet(
                        street_name=street,
                        latitude=best.latitude,
                        longitude=best.longitude,
                        address=best.address,
                        town=best.town,
                        candidate_count=len(street_candidates),
                    )
                )
                streets_in_validation.add(street)

        invalid_streets = [s for s in original_streets if s not in streets_in_validation]
        return validated_streets, invalid_streets

    def _distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat_diff = abs(lat2 - lat1) * self.MILES_PER_DEGREE_LAT
        lon_diff = abs(lon2 - lon1) * self.MILES_PER_DEGREE_LON
        return (lat_diff**2 + lon_diff**2) ** 0.5

    def _calculate_centroid(self, points: List[ValidatedStreet | GeocodingCandidate]) -> Tuple[float, float]:
        if not points:
            return (0.0, 0.0)
        avg_lat = sum(p.latitude for p in points) / len(points)
        avg_lon = sum(p.longitude for p in points) / len(points)
        return (avg_lat, avg_lon)

    def _calculate_radius(self, center: Tuple[float, float], points: List[ValidatedStreet]) -> float:
        max_distance = 0.0
        for p in points:
            d = self._distance(center[0], center[1], p.latitude, p.longitude)
            max_distance = max(max_distance, d)
        return max_distance

    async def _reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": self.user_agent}) as client:
                resp = await client.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={"format": "json", "lat": lat, "lon": lon, "zoom": 18},
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("display_name")
        except Exception as e:
            logger.warning(f"Reverse geocode failed: {e}")
            return None

    def _calculate_confidence(self, num_validated: int, num_total: int, radius_miles: float) -> float:
        coverage = num_validated / num_total if num_total > 0 else 0.0
        radius_penalty = min(radius_miles / self.CLUSTERING_RADIUS_MILES, 1.0)
        confidence = (coverage * 0.7) + ((1.0 - radius_penalty) * 0.3)
        return max(0.0, min(1.0, confidence))


def initialize_clustering_validator() -> StreetClusteringValidator:
    """Construct the in-module StreetClusteringValidator (no external imports)."""
    logger.info("StreetClusteringValidator initialized (in-module implementation)")
    return StreetClusteringValidator()


async def geocode_streets(validator: StreetClusteringValidator, streets: List[str], county: str, state: str, town: str) -> Dict:
    """Geocode using the in-module validator and shape output for downstream steps."""
    cluster_result = await validator.validate_and_cluster(
        streets=streets, county=county, state=state, town=town or None
    )
    return {
        "validated_streets": [
            {
                "street_name": s.street_name,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "address": s.address,
                "town": s.town,
                "candidate_count": s.candidate_count,
            }
            for s in cluster_result.validated_streets
        ],
        "invalid_streets": cluster_result.invalid_streets,
        "primary_town": cluster_result.primary_town,
        "cluster_center_lat": cluster_result.cluster_center_lat,
        "cluster_center_lon": cluster_result.cluster_center_lon,
        "final_address": cluster_result.final_address,
        "cluster_radius_miles": cluster_result.cluster_radius_miles,
        "confidence": cluster_result.confidence,
        "geocoding_stats": cluster_result.geocoding_stats,
    }


async def process_deed_geolocation(deed_record: Dict, validator: StreetClusteringValidator) -> Dict:
    """Process geolocation for a single deed record."""
    deed_id = deed_record.get("deed_id")

    # Check cache
    if ENABLE_CACHE:
        cache_key = get_cache_key("step4", deed_id)
        cached = load_from_cache(cache_key)
        if cached:
            logger.info(f"Deed {deed_id}: Loaded from cache")
            return cached

    streets = deed_record.get("extracted_streets", [])
    if not streets:
        logger.warning(f"Deed {deed_id}: No streets found")
        deed_record["geolocation"] = None
        deed_record["step4_completed"] = True
        return deed_record

    county = deed_record.get("county", "")

    # Determine town: prefer deed_record['town'], else derive from scraper_results
    town = deed_record.get("town")
    if not town:
        scraper_results = deed_record.get("scraper_results", [])
        for s in scraper_results:
            city_town = s.get("metadata", {}).get("search_result_info", {}).get("town")
            if city_town:
                town = city_town
                break
    if not town:
        logger.warning(f"Deed {deed_id}: No town information found")
        town = ""
    state = "Massachusetts"
    logger.info(f"Deed {deed_id}: Geocoding {len(streets)} streets in {town}, {county}")

    geolocation_result = await geocode_streets(validator, streets, county, state, town)

    deed_record["geolocation"] = geolocation_result
    deed_record["step4_completed"] = True

    if ENABLE_CACHE:
        save_to_cache(cache_key, deed_record)

    return deed_record


async def run_step4_async(input_file: Path = STEP3_OUTPUT, output_file: Path = STEP4_OUTPUT) -> Dict[str, Dict]:
    """Run Step 4 asynchronously over all deeds."""
    logger.info(f"Starting Step 4: Geolocation")
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")

    try:
        deed_data = load_json(input_file)
        logger.info(f"Loaded {len(deed_data)} deed records")

        validator = initialize_clustering_validator()

        processed_data: Dict[str, Dict] = {}
        total = len(deed_data)
        for idx, (deed_id, deed_record) in enumerate(deed_data.items(), 1):
            logger.info(f"Processing deed {deed_id} ({idx}/{total})")
            processed_data[deed_id] = await process_deed_geolocation(deed_record, validator)

        save_json(processed_data, output_file)
        logger.info(f"Step 4 completed. Output saved to {output_file}")
        return processed_data

    except Exception as e:
        logger.error(f"Error in Step 4: {e}", exc_info=True)
        raise


def run_step4(input_file: Path = STEP3_OUTPUT, output_file: Path = STEP4_OUTPUT) -> Dict[str, Dict]:
    """Sync wrapper around the async runner."""
    import asyncio
    return asyncio.run(run_step4_async(input_file, output_file))


if __name__ == "__main__":
    run_step4()
