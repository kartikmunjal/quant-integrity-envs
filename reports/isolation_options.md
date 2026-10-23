# Isolation options diagnostic

Date: 2026-10-21 (America/Denver)

P2b was not started. This diagnostic was read-only apart from creating this report.

## Host

- OS: macOS 14.4, build 23E214
- Kernel: Darwin 23.4.0, ARM64
- Hardware: MacBook Air `Mac14,2`, Apple M2
- Environment: not WSL and not a Linux container. Available evidence indicates a native macOS
  host rather than a VM, although the execution sandbox blocked some low-level probes.

## Privileges

- Root: no; the user ID is 501.
- Sudo: the account belongs to the macOS `admin` group and `/usr/bin/sudo` is installed
  setuid-root, but this session cannot invoke it (`operation not permitted`). Codex therefore has
  no usable sudo access.

## Runtime discovery

The requested `which docker podman bwrap nsjail unshare runsc` command produced:

```text
docker not found
podman not found
bwrap not found
nsjail not found
unshare not found
runsc not found
```

## Unprivileged user namespaces

- Linux user namespaces are not supported by the Darwin kernel.
- `kernel.unprivileged_userns_clone` is an unknown sysctl.
- `unshare` is absent.
- Bubblewrap, nsjail, runsc, and Linux namespace isolation therefore cannot operate natively on
  this host.

## Installation feasibility

- `/usr/bin/apt` is Apple's Java annotation-processing tool, not Debian's package manager. It
  cannot install these runtimes.
- `pip` works, and Python package registries are allowed by `AGENTS.md`.
- Pip can install Docker or Podman client libraries, but not a container daemon, Linux kernel
  namespaces, bubblewrap, nsjail, or runsc. A pip installation cannot provide the required
  security boundary.
- Homebrew exists, but no container runtime is installed. Homebrew could theoretically install
  Podman, Colima, or Docker-related components because package registries are allowed. Doing so
  would write outside this repository and create or manage a Linux VM; it was not attempted or
  authorized by the read-only diagnostic.

## Recommendation

Path **(a), a real container runtime**, is the only feasible implementation path, but it must first
be installed and configured outside this task. Suitable macOS options include Podman Machine,
Colima with the Docker CLI, or Docker Desktop; all use a Linux VM underneath.

Path **(b), bubblewrap-style namespace isolation**, is not feasible natively on macOS. Path **(c),
neither**, describes the machine's current state but is not a viable implementation path for P2b.

