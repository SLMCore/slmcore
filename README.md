# slmcore architecture

`slmcore` is organized around a central state/runtime engine plus reusable SLM
capabilities and integration layers.

## Central engine

The architectural backbone lives in `engine/`:

```text
ParamSpec / param_field
        ↓
     StateModel
        ↓
GroupStateModel / ItemState / ParameterSetState
        ↓
   SLMSectionState
        ↑
     Registries
        ↓
 SLMSectionRuntime
        ↓
    SLMRuntime
```

The main engine packages are:

- `engine/parameters/`: parameter specifications, links, units, and converters.
- `engine/state/`: generic state models, groups, items, topology, and loading paths.
- `engine/section/`: one SLM section's state, geometry, snapshots, artifacts, and runtime.
- `engine/registry.py`: registration models/decorators and the explicit standard-registration composition point.
- `engine/transition.py`: immutable descriptions of committed state changes.
- `engine/runtime.py`: aggregate SLM runtime and composed artifacts.
- `engine/device.py`: physical SLM identity and geometry.

Registration declarations stay beside the implementations they describe. The
standard registrations are assembled by
`engine.registry.load_default_registrations()` from `patterns/`, `cgh/targets/`,
and `cgh/computations/`.

## Capabilities

- `patterns/`: analytic patterns and aberrations.
- `cgh/`: targets, CGH algorithms, localization, metrics, and feedback.
- `calibration/`: section/plane calibration models and storage.
- `measurement/`: host-neutral image measurement records.
- `corrections/`: device correction-pattern and 2π lookup/storage.

## Integration layers

- `setup/`: canonical installed-SLM setup model (identity, geometry, sections, corrections, and optional hardware description).
- `workspace/`: reusable config/calibration/correction/preference persistence rooted at one application data directory.
- `config/`: configuration models, serialization, migration, and repositories.
- `application/`: runtime construction from a canonical `SLMSetup`.
- `host/`: optional host capability contracts and callbacks.
- `qt/`: reusable Qt panels, sessions, views, and interaction controllers.

The root `slmcore` package remains the convenient public facade for commonly
used types. Internal architectural modules use the `slmcore.engine.*` paths.

## Canonical setup and workspace

`SLMSetup` is the public setup contract. It stores the physical identity and
geometry plus the declared section layout and optional installed correction /
hardware information. Section geometries are derived by slmcore rather than by
the embedding host. `SLMIdentity.serial_number` is mandatory and is the stable
physical namespace for persistent workspace data; `key` remains the logical
runtime identifier.

`SLMWorkspace(root)` provides the standard persistence implementation for a
standalone or embedded application. Configs are stored per serial number, while
calibration definitions and preferences are shared by the workspace. Correction
resources preserve the established resolution behavior: an existing configured
preferred directory wins, otherwise an existing workspace correction directory
for the serial number is used; missing correction directories are not created
automatically.

The normal Qt composition is therefore:

```python
workspace = SLMWorkspace(data_dir)
factory = SLMQtSessionFactory(workspace=workspace)
session, panel = factory.create(setup=setup, host_services=services)
```

Explicit host preference capabilities still override the workspace defaults.
