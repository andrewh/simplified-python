"""Load and validate an application configuration file, falling back to defaults."""

import json
import tempfile
from pathlib import Path

type Settings = dict[str, object]

DEFAULTS: Settings = {"host": "localhost", "port": 8080, "debug": False}


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, host: str, port: int, debug: bool):
        self.host = host
        self.port = port
        self.debug = debug

    @classmethod
    def from_settings(cls, settings: Settings) -> Config:
        unknown = sorted(set(settings) - set(DEFAULTS))
        if unknown:
            raise ConfigError(f"unknown settings: {', '.join(unknown)}")
        merged = {**DEFAULTS, **settings}
        port = merged["port"]
        if not isinstance(port, int):
            raise ConfigError(f"port must be an integer, got {port!r}")
        if port < 1 or port > 65535:
            raise ConfigError(f"port {port} is out of range")
        return cls(str(merged["host"]), port, bool(merged["debug"]))

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"


def load_config(path: Path) -> Config:
    try:
        with path.open(encoding="utf-8") as handle:
            settings = json.load(handle)
    except FileNotFoundError:
        return Config.from_settings({})
    except json.JSONDecodeError as error:
        raise ConfigError(f"{path.name} is not valid JSON") from error
    return Config.from_settings(settings)


def write_samples(folder: Path) -> list[Path]:
    good = folder / "good.json"
    good.write_text(json.dumps({"port": 9000, "debug": True}), encoding="utf-8")
    typo = folder / "typo.json"
    typo.write_text(json.dumps({"prot": 9000}), encoding="utf-8")
    broken = folder / "broken.json"
    broken.write_text("{port: 9000}", encoding="utf-8")
    return [good, folder / "missing.json", typo, broken]


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        for path in write_samples(Path(directory)):
            try:
                config = load_config(path)
            except ConfigError as error:
                print(f"{path.name}: error: {error}")
                continue
            print(f"{path.name}: {config.address} debug={config.debug}")


if __name__ == "__main__":
    main()
