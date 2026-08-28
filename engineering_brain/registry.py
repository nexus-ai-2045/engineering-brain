from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_REGISTRY = PACKAGE_ROOT / "data" / "adoption-units.yaml"
DEFAULT_TECHNOLOGY_SOURCES = PACKAGE_ROOT / "data" / "technology-sources.yaml"


@dataclass(frozen=True)
class AdoptionUnit:
    id: str
    status: str
    source_refs: tuple[str, ...]
    applies_when: tuple[str, ...]
    timing: tuple[str, ...]
    boundary: str
    route: str
    guarantee_tier: str
    checks: tuple[dict[str, Any], ...]
    insufficient_if: tuple[str, ...]


@dataclass(frozen=True)
class TechnologySource:
    id: str
    domain: str
    status: str
    source_refs: tuple[str, ...]
    use_when: tuple[str, ...]
    adoption_route: str
    gate_hint: str
    insufficient_if: tuple[str, ...]


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "null":
        return None
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        body = value[1:-1].strip()
        if not body:
            return []
        return [part.strip().strip('"') for part in body.split(",")]
    return value


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    """Load the constrained YAML shape used by this repository.

    The registry intentionally uses a small YAML subset so the CLI has no
    runtime dependency on PyYAML.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    data: dict[str, Any] = {}
    current: dict[str, Any] | None = None
    current_section: str | None = None
    current_list_key: str | None = None
    current_check: dict[str, Any] | None = None

    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        text = raw.strip()
        if indent == 0 and text.startswith("version:"):
            data["version"] = int(text.split(":", 1)[1].strip())
            continue
        if indent == 0 and text.startswith("updated_at:"):
            data["updated_at"] = _parse_scalar(text.split(":", 1)[1])
            continue
        if indent == 0 and text.startswith("profile_load_mode:"):
            data["profile_load_mode"] = _parse_scalar(text.split(":", 1)[1])
            continue
        if indent == 0 and text in {"units:", "sources:", "profiles:"}:
            current_section = text[:-1]
            data[current_section] = []
            continue
        if indent == 2 and text.startswith("- id:"):
            if current_section is None:
                raise ValueError("list item found before registry section")
            current = {"id": text.split(":", 1)[1].strip()}
            data[current_section].append(current)
            current_list_key = None
            current_check = None
            continue
        if current is None or indent < 4:
            continue
        if indent == 4 and ":" in text:
            key, raw_value = text.split(":", 1)
            value = raw_value.strip()
            if value:
                current[key] = _parse_scalar(value)
                current_list_key = None
                current_check = None
            else:
                current[key] = []
                current_list_key = key
                current_check = None
            continue
        if text.startswith("- ") and current_list_key:
            item = text[2:].strip()
            if current_list_key == "checks":
                current_check = {}
                current[current_list_key].append(current_check)
                if ":" in item:
                    key, raw_value = item.split(":", 1)
                    current_check[key] = _parse_scalar(raw_value)
            elif isinstance(current[current_list_key], list):
                current[current_list_key].append(_parse_scalar(item))
            continue
        if indent == 8 and current_list_key == "checks" and current_check is not None and ":" in text:
            key, raw_value = text.split(":", 1)
            current_check[key] = _parse_scalar(raw_value)

    return data


def adoption_units(path: Path = DEFAULT_REGISTRY) -> list[AdoptionUnit]:
    units = []
    for raw in load_registry(path)["units"]:
        validate_unit(raw)
        units.append(
            AdoptionUnit(
                id=raw["id"],
                status=raw["status"],
                source_refs=tuple(raw["source_refs"]),
                applies_when=tuple(raw["applies_when"]),
                timing=tuple(raw["timing"]),
                boundary=raw["boundary"],
                route=raw["route"],
                guarantee_tier=raw["guarantee_tier"],
                checks=tuple(raw["checks"]),
                insufficient_if=tuple(raw["insufficient_if"]),
            )
        )
    return units


def technology_sources(path: Path = DEFAULT_TECHNOLOGY_SOURCES) -> list[TechnologySource]:
    sources = []
    for raw in load_registry(path)["sources"]:
        validate_technology_source(raw)
        sources.append(
            TechnologySource(
                id=raw["id"],
                domain=raw["domain"],
                status=raw["status"],
                source_refs=tuple(raw["source_refs"]),
                use_when=tuple(raw["use_when"]),
                adoption_route=raw["adoption_route"],
                gate_hint=raw["gate_hint"],
                insufficient_if=tuple(raw["insufficient_if"]),
            )
        )
    return sources


def select_technology_sources(domain: str | None = None) -> list[TechnologySource]:
    sources = technology_sources()
    if domain is None:
        return sources
    normalized = domain.lower()
    return [
        source
        for source in sources
        if source.domain.lower() == normalized or normalized in {item.lower() for item in source.use_when}
    ]


def validate_unit(raw: dict[str, Any]) -> None:
    required = {
        "id",
        "status",
        "source_refs",
        "applies_when",
        "timing",
        "boundary",
        "route",
        "guarantee_tier",
        "checks",
        "insufficient_if",
    }
    missing = sorted(required.difference(raw))
    if missing:
        raise ValueError(f"adoption unit {raw.get('id', '<unknown>')} missing fields: {', '.join(missing)}")
    if raw["status"] not in {"adopted", "candidate", "hold", "rejected"}:
        raise ValueError(f"adoption unit {raw['id']} has invalid status: {raw['status']}")
    for list_key in ("source_refs", "applies_when", "timing", "checks", "insufficient_if"):
        if not raw[list_key]:
            raise ValueError(f"adoption unit {raw['id']} has empty {list_key}")
    if not str(raw["guarantee_tier"]).startswith("G"):
        raise ValueError(f"adoption unit {raw['id']} has invalid guarantee_tier")


def validate_technology_source(raw: dict[str, Any]) -> None:
    required = {
        "id",
        "domain",
        "status",
        "source_refs",
        "use_when",
        "adoption_route",
        "gate_hint",
        "insufficient_if",
    }
    missing = sorted(required.difference(raw))
    if missing:
        raise ValueError(f"technology source {raw.get('id', '<unknown>')} missing fields: {', '.join(missing)}")
    if raw["status"] not in {"adopted", "candidate", "hold", "rejected"}:
        raise ValueError(f"technology source {raw['id']} has invalid status: {raw['status']}")
    for list_key in ("source_refs", "use_when", "insufficient_if"):
        if not raw[list_key]:
            raise ValueError(f"technology source {raw['id']} has empty {list_key}")


def select_units(triggers: list[str], *, include_candidates: bool = False) -> list[AdoptionUnit]:
    normalized = {trigger.lower() for trigger in triggers}
    selected = []
    for unit in adoption_units():
        if unit.status == "candidate" and not include_candidates:
            continue
        if normalized.intersection({item.lower() for item in unit.applies_when}):
            selected.append(unit)
    return selected
