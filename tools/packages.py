import polars as pl
from pydantic import BaseModel
from typing import List, Optional
from packaging.version import Version, InvalidVersion


class Package(BaseModel):
    host: Optional[str] = None
    name: str
    version: str
    version_major: Optional[int] = None
    version_minor: Optional[int] = None
    version_micro: Optional[int] = None
    release: Optional[str] = None
    arch: Optional[str] = None
    repo: Optional[str] = None
    os_family: Optional[str] = None   # "rhel" | "debian"
    epoch: Optional[str] = None       # RPM epoch if present


def _parse_version_parts(version: str) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """Try to extract major/minor/micro from a version string."""
    try:
        v = Version(version)
        r = v.release
        return (
            r[0] if len(r) > 0 else None,
            r[1] if len(r) > 1 else None,
            r[2] if len(r) > 2 else None,
        )
    except InvalidVersion:
        # Fall back to manual split for RPM/Debian versions
        parts = version.split(".")
        def try_int(s):
            try:
                return int(s.split("-")[0].split("+")[0].split("~")[0])
            except ValueError:
                return None
        return (
            try_int(parts[0]) if len(parts) > 0 else None,
            try_int(parts[1]) if len(parts) > 1 else None,
            try_int(parts[2]) if len(parts) > 2 else None,
        )


def parse_rhel(output: str, host: Optional[str] = None) -> List[Package]:
    """Parses 'rpm -qa' output (name-version-release.arch format)."""
    packages = []
    for line in output.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        # Split off architecture
        arch = None
        if "." in line:
            base, arch = line.rsplit(".", 1)
        else:
            base = line

        # Handle RPM epoch (e.g. 2:curl-7.76.1-26.el9)
        epoch = None
        if ":" in base.split("-")[0] if "-" in base else base:
            epoch_part, base = base.split(":", 1)
            epoch = epoch_part

        # Split name, version, release
        release = None
        if "-" in base:
            parts = base.split("-")
            if len(parts) >= 3:
                name = "-".join(parts[:-2])
                version = parts[-2]
                release = parts[-1]
            elif len(parts) == 2:
                name = parts[0]
                version = parts[1]
            else:
                name = base
                version = ""
        else:
            name = base
            version = ""

        major, minor, micro = _parse_version_parts(version)

        packages.append(Package(
            host=host,
            name=name,
            version=version,
            version_major=major,
            version_minor=minor,
            version_micro=micro,
            release=release,
            arch=arch,
            epoch=epoch,
            os_family="rhel",
        ))
    return packages


def parse_debian(output: str, host: Optional[str] = None) -> List[Package]:
    """Parses 'dpkg -l' output for installed packages (ii lines)."""
    packages = []
    for line in output.strip().splitlines():
        if not line.startswith("ii"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue

        name = parts[1]
        version = parts[2]
        arch = parts[3] if len(parts) > 3 else None

        # Strip epoch from version (e.g. 2:7.88.1-10 -> 7.88.1-10)
        epoch = None
        if ":" in version:
            epoch, version = version.split(":", 1)

        # Debian version: upstream-debian (e.g. 7.88.1-10), split off debian revision
        release = None
        if "-" in version:
            version, release = version.rsplit("-", 1)

        major, minor, micro = _parse_version_parts(version)

        packages.append(Package(
            host=host,
            name=name,
            version=version,
            version_major=major,
            version_minor=minor,
            version_micro=micro,
            release=release,
            arch=arch,
            epoch=epoch,
            os_family="debian",
        ))
    return packages


def packages_to_dataframe(pkgs: List[Package]) -> pl.DataFrame:
    """Convert list of Package objects to Polars DataFrame."""
    df = pl.DataFrame([p.dict() for p in pkgs])

    for col in ["host", "name", "arch", "repo", "os_family"]:
        if col in df.columns:
            df = df.with_columns(df[col].cast(pl.Categorical))

    for col in ["version_major", "version_minor", "version_micro"]:
        if col in df.columns:
            df = df.with_columns(df[col].cast(pl.Int32))

    return df