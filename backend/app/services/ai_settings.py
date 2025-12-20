DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"


def normalize_model_name(name: str) -> str:
    if name.startswith("models/"):
        return name.split("/", 1)[1]
    return name


def resolve_model(model: str | None) -> str:
    if model and model.strip():
        return model.strip()
    return DEFAULT_GEMINI_MODEL


def choose_model(
    available_models: list[str],
    requested_model: str | None,
    current_model: str | None,
) -> str:
    normalized = [normalize_model_name(item) for item in available_models]
    requested = normalize_model_name(requested_model) if requested_model else None
    current = normalize_model_name(current_model) if current_model else None

    if requested and requested in normalized:
        return requested
    if current and current in normalized:
        return current
    if DEFAULT_GEMINI_MODEL in normalized:
        return DEFAULT_GEMINI_MODEL
    if normalized:
        return normalized[0]
    return DEFAULT_GEMINI_MODEL
