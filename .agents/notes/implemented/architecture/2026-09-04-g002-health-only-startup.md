# Agent Note: G002 Health-Only Startup and Database Namespace

Status: implemented — local startup exposes only the target health entry and every active target configuration uses the isolated `clawith_target` database namespace.

## Problem

The target Settings owner reads `backend/.env`, but repository setup and restart scripts still read or created a root `.env`, prepared the legacy `clawith` database, ran Alembic and checkpoint installers, started legacy Runtime and Frontend processes, and advertised a complete product. Compose, CI/CD, deploy, and Helm configuration also pointed active Backend consumers at the legacy database. Those paths could start incompatible code against legacy state and made a health-only G002 skeleton appear product-ready.

## Decision

`backend/.env.example` is the sole local Backend template. `setup.sh` synchronizes only supported target keys into `backend/.env`, forces its complete async PostgreSQL URL to `clawith_target`, prepares the `clawith` role and `clawith_target` database, and installs Backend dependencies. The Settings owner independently requires the parsed database name to equal `clawith_target` and rejects query keys that can override database, host, port, or credential identity for direct values, OS environment values, and dotenv values before application or Alembic consumers can create an engine. Rejection diagnostics identify only the required invariant and offending key names; they never render the URL, query values, or password. Setup does not read or create a root `.env`, mutate schemas, run Alembic, install checkpoints, seed, repair, or start services.

`restart.sh` requires `backend/.env` and stores the launched PID together with its process start identity. Before signaling a recorded PID it requires both that start identity and the `uvicorn app.main:app --workers 1` command marker to match, so stale evidence cannot signal a reused process. EXIT, INT, and TERM cleanup is armed immediately after launch; the child resets inherited signal state, cleanup sends TERM and waits for a bounded interval, removes evidence only after terminal state, and retains evidence when ownership or termination cannot be proved. Health success alone disarms cleanup and leaves the live process evidence for the next owned restart. The script does not auto-select Docker, start the Frontend or product workers, inject legacy Runtime variables, or execute migrations. The public README describes this health-only state and treats Docker, CI/CD, deploy, and Helm as deferred paths rather than supported product startup.

Every retained Backend database value in local Compose, CI/CD, deploy, and Helm configuration uses `clawith_target`. All Compose services require the explicit `deferred-product` profile, and the Helm chart defaults `g002Deferred` to true so it renders no resources. Legacy migration, deployment, release, and upgrade CI jobs are replaced by current G002 architecture, full Backend, static, and collection gates instead of adapting their old behavior. Checked-in Alembic revisions remain unchanged legacy evidence until G008. Alembic is never an application startup action; a future reviewed target baseline remains an explicit operator-only mutation.

Every public and operator-facing README, contribution guide, deployment guide, Helm guide, and Backend Alembic guide states the G002 health-only boundary and contains no executable legacy migration, Docker, Helm, Frontend, root-dotenv, or legacy-database procedure. `backend/alembic.ini` names `clawith_target` and warns that operator migration remains unavailable until G008. Localized documentation links to the current root README instead of retaining translated product-start instructions.

## Alternatives considered

**Keep root `.env` as a shared local and Compose template.** Rejected because target Settings deliberately owns one dotenv path under `backend/` and must not inherit unrelated legacy variables.

**Run the existing Alembic chain during setup or restart.** Rejected because it is frozen legacy evidence, not the target baseline, and startup must not mutate schema.

**Keep the full product restart and describe unavailable features as degraded.** Rejected because the target currently mounts only `/api/health`; starting Frontend, workers, connectors, or Docker would misrepresent readiness and preserve deleted Runtime contracts.

**Repair legacy CI migration and upgrade workflows against `clawith_target`.** Rejected because those workflows test removed compatibility behavior; G002 CI must execute current target gates instead.

## Consequences

Local setup requires a reachable PostgreSQL administrator and fails explicitly when required commands or `backend/.env.example` are missing. Existing supported target dotenv values are preserved, unsupported legacy keys are dropped, and the database URL is reset to the isolated target namespace. Startup proves only Backend process and health-route readiness. Product behavior, schema readiness, deployment, and live acceptance remain unavailable.

## Verification

Architecture tests execute setup and restart against fake process and PostgreSQL boundaries, validate the single dotenv owner and target database, reject migration/bootstrap/legacy Runtime commands, and scan every active database configuration path. Restart tests exercise stale PID reuse, early identity-capture failure, timeout, INT, TERM, normal health, child failure, and a TERM-ignoring child with retained evidence. Startup and CI guards parse executable shell or YAML command positions and expand chained assignments; inert prose does not decide behavior. Operator-document guards inspect fenced executable instructions across an exact path inventory and separately reject active legacy database URLs while allowing inert warnings. Shell syntax, Backend tests, Ruff, Pyright, Compose rendering, YAML parsing, Helm rendering where available, and repository architecture guards provide local evidence. No check in this change proves a live database, container, Kubernetes cluster, migration, or product workflow.
