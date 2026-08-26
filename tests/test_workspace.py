from pathlib import Path

from slmcore import (
    DEFAULT_REGISTRIES,
    SLMCorrectionSetup,
    SLMGeometry,
    SLMIdentity,
    SLMSectionsSetup,
    SLMSetup,
    SLMWorkspace,
    SLMWorkspaceLayout,
    SectionSplitLayout,
)


def _setup(*,key="slm",serial="SER123",corrections=None):
    return SLMSetup(
        identity=SLMIdentity(key,serial),
        geometry=SLMGeometry(width=16,height=8,pixel_size_um=1.0),
        sections=SLMSectionsSetup(
            layout=SectionSplitLayout(n_sections=1),
        ),
        corrections=corrections,
    )


def test_workspace_namespaces_persistent_resources_by_serial(tmp_path):
    workspace = SLMWorkspace(tmp_path)
    setup = _setup(key="renamable_key",serial="PHYSICAL-001")
    repository = workspace.config_repository(setup,DEFAULT_REGISTRIES)

    assert repository.directory == tmp_path / "configs" / "PHYSICAL-001"
    assert repository.directory.is_dir()
    assert "renamable_key" not in str(repository.directory)


def test_workspace_layout_can_preserve_host_directory_names(tmp_path):
    workspace = SLMWorkspace(
        tmp_path,
        layout=SLMWorkspaceLayout(corrections="Corrections"),
    )
    setup = _setup(
        corrections=SLMCorrectionSetup(wavelength_table_file="table.json"),
    )
    default = tmp_path / "Corrections" / "SER123"
    default.mkdir(parents=True)

    store = workspace.correction_store(setup)
    assert store is not None
    assert store.directory == default
    assert store.wavelength_table_file == "table.json"


def test_workspace_prefers_existing_configured_correction_directory(tmp_path):
    preferred = tmp_path / "manufacturer"
    preferred.mkdir()
    fallback = tmp_path / "corrections" / "SER123"
    fallback.mkdir(parents=True)
    setup = _setup(
        corrections=SLMCorrectionSetup(
            preferred_directory=preferred,
            wavelength_table_file="table.json",
        ),
    )

    store = SLMWorkspace(tmp_path).correction_store(setup)
    assert store is not None
    assert store.directory == preferred


def test_workspace_falls_back_when_configured_correction_directory_is_missing(tmp_path):
    fallback = tmp_path / "corrections" / "SER123"
    fallback.mkdir(parents=True)
    setup = _setup(
        corrections=SLMCorrectionSetup(
            preferred_directory=tmp_path / "missing",
        ),
    )

    store = SLMWorkspace(tmp_path).correction_store(setup)
    assert store is not None
    assert store.directory == fallback


def test_workspace_does_not_create_missing_correction_directory(tmp_path):
    setup = _setup(corrections=SLMCorrectionSetup())
    workspace = SLMWorkspace(tmp_path)
    expected = tmp_path / "corrections" / "SER123"

    assert workspace.correction_store(setup) is None
    assert not expected.exists()


def test_workspace_preferences_are_serial_scoped(tmp_path):
    workspace = SLMWorkspace(tmp_path)
    first = _setup(key="first",serial="SER123")
    renamed = _setup(key="renamed",serial="SER123")

    first_services = workspace.default_host_services(first)
    first_services.configuration_preferences.set("startup.h5")
    first_services.calibration_preferences.set("sec_0","Sample")
    first_services.section_view_preferences.set("horizontal")

    renamed_services = workspace.default_host_services(renamed)
    assert renamed_services.configuration_preferences.get() == "startup.h5"
    assert renamed_services.calibration_preferences.get("sec_0") == "Sample"
    assert renamed_services.section_view_preferences.get() == "horizontal"
    assert (tmp_path / "preferences.json").is_file()
