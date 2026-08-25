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

- `config/`: configuration models, serialization, migration, and repositories.
- `application/`: host-supplied SLM definitions and runtime construction.
- `host/`: host service contracts and callbacks.
- `qt/`: reusable Qt panels, sessions, views, and interaction controllers.

The root `slmcore` package remains the convenient public facade for commonly
used types. Internal architectural modules use the `slmcore.engine.*` paths.
