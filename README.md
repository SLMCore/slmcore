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

- `setup/`: canonical installed-SLM setup and startup-preference models plus JSON helpers.
- `workspace/`: standard config/calibration/correction resource layout rooted at one application data directory.
- `config/`: configuration models, serialization, migration, and repositories.
- `application/`: runtime construction from a canonical `SLMSetup`.
- `host/`: optional host capability contracts and callbacks.
- `qt/`: reusable Qt panels, sessions, views, and interaction controllers.

The root `slmcore` package remains the convenient public facade for commonly
used types. Internal architectural modules use the `slmcore.engine.*` paths.

## Canonical setup and workspace

`SLMSetup` is the public installed-SLM contract. It stores logical/physical
identity, human-readable display name, geometry, declared section layout and
optional hardware information. Section geometries are derived by slmcore rather
than by the embedding host. `SLMIdentity.serial_number` is mandatory and is the
stable physical namespace for persistent workspace resources; `key` remains the
logical runtime identifier. `display_name` is presentation-only and does not
participate in identity matching.

`SLMStartupPreferences` stores persistent defaults applied when constructing a
session: startup config, default active plane per section and section display
mode. A canonical standalone JSON file contains both `setup` and
`startup_preferences`. Hosts with a larger setup format may embed the same two
objects and use `to_dict()` / `from_dict()` directly.

`SLMWorkspace(root)` is the standard runtime-resource layout:

```text
<root>/
├── configs/<serial>/
├── corrections/<serial>/
└── calibrations/
```

Normally the host supplies only `root`; slmcore owns the rest. Advanced hosts
may override `configs_dir`, `corrections_dir` and/or `calibrations_dir` when
constructing the workspace. Correction lookup uses the standard per-serial
directory and `wavelength.json`; missing correction data simply follows the
normal correction-store fallback behavior.

The normal Qt composition is therefore:

```python
workspace = SLMWorkspace(data_dir)
factory = SLMQtSessionFactory(workspace=workspace)
session, panel = factory.create(
    setup=setup,
    startup_preferences=startup_preferences,
    setup_file=setup_file,  # standard standalone JSON persistence
    host_services=services,
)
```

If the host owns a larger setup file, it omits `setup_file` and supplies
`on_startup_preferences_changed`; slmcore owns preference semantics while the
host owns how its setup file is rewritten.
