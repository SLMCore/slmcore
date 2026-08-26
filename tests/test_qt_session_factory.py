import pytest

from slmcore import (
    DEFAULT_REGISTRIES,
    SLMGeometry,
    SLMIdentity,
    SLMSectionsSetup,
    SLMSetup,
    SLMWorkspace,
)
from slmcore.application import SLMRuntimeFactory
from slmcore.host import (
    ConfigurationPreferences,SectionViewPreferences,SLMDeviceProvider,
    SLMHostServices,
)
from slmcore.engine.section import SectionSplitLayout


def _app():
    pytest.importorskip("qtpy")
    pytest.importorskip("pyqtgraph")
    try:
        from qtpy import QtWidgets
    except Exception as error:
        pytest.skip("Qt bindings are unavailable: %s" % error)
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def _setup():
    return SLMSetup(
        identity=SLMIdentity("slm","SER123"),
        geometry=SLMGeometry(width=24,height=12,pixel_size_um=1.0),
        sections=SLMSectionsSetup(
            layout=SectionSplitLayout(n_sections=2,axis="x"),
            customizable=True,
        ),
    )


def _runtime(setup,repository=None):
    return SLMRuntimeFactory(
        setup=setup,
        registries=DEFAULT_REGISTRIES,
        config_repository=repository,
    ).create_default()


def test_session_factory_constructs_default_session_and_panel():
    _app()
    from slmcore.qt import SLMPanel,SLMQtSession,SLMQtSessionFactory

    setup = _setup()
    factory = SLMQtSessionFactory()
    session,panel = factory.create(
        setup=setup,
        display_name="Test SLM",
    )
    try:
        assert isinstance(session,SLMQtSession)
        assert isinstance(panel,SLMPanel)
        assert session.panel is panel
        assert session.runtime_factory.setup is setup
        assert session.runtime_factory.registries is DEFAULT_REGISTRIES
        assert session.config_repository is None
        assert session.current_config_path is None
        assert session.display_name == "Test SLM"
    finally:
        session.dispose()
        panel.deleteLater()


def test_session_factory_uses_workspace_startup_config_and_view_preference(tmp_path):
    _app()
    from slmcore.qt import SectionsDisplayMode,SLMQtSessionFactory

    setup = _setup()
    workspace = SLMWorkspace(tmp_path)
    repository = workspace.config_repository(setup,DEFAULT_REGISTRIES)
    runtime = _runtime(setup,repository)
    repository.save("startup.h5",runtime.create_config(),"startup",overwrite=False)
    workspace.preference_store.set_startup_config("SER123","startup.h5")
    workspace.preference_store.set_section_display_mode("SER123","horizontal")

    factory = SLMQtSessionFactory(workspace=workspace)
    session,panel = factory.create(setup=setup)
    try:
        assert session.current_config_path == str(repository.resolve("startup.h5"))
        assert session.config_repository is repository
        assert session.config_repository.directory == tmp_path / "configs" / "SER123"
        assert session.config_repository.registries is DEFAULT_REGISTRIES
        assert panel.section_host.display_mode == SectionsDisplayMode.HORIZONTAL
    finally:
        session.dispose()
        panel.deleteLater()


def test_explicit_host_preferences_override_workspace_defaults(tmp_path):
    _app()
    from slmcore.qt import SectionsDisplayMode,SLMQtSessionFactory

    setup = _setup()
    workspace = SLMWorkspace(tmp_path)
    workspace.preference_store.set_section_display_mode("SER123","tabs")
    services = SLMHostServices(
        section_view_preferences=SectionViewPreferences(
            get_display_mode=lambda:"horizontal",
            set_display_mode=lambda _value:None,
        ),
    )
    session,panel = SLMQtSessionFactory(workspace=workspace).create(
        setup=setup,host_services=services,
    )
    try:
        assert panel.section_host.display_mode == SectionsDisplayMode.HORIZONTAL
    finally:
        session.dispose()
        panel.deleteLater()


def test_session_factory_surfaces_startup_warning_without_workspace():
    _app()
    from slmcore.qt import SLMQtSessionFactory

    setup = _setup()
    services = SLMHostServices(
        configuration_preferences=ConfigurationPreferences(
            get_startup_config=lambda:"missing.h5",
            set_startup_config=lambda _value:None,
        ),
    )
    session,panel = SLMQtSessionFactory().create(
        setup=setup,host_services=services,
    )
    try:
        assert "configuration storage is not configured" in (
            panel.status_label.full_text().lower()
        )
    finally:
        session.dispose()
        panel.deleteLater()


def test_session_factory_does_not_initialize_device():
    _app()
    from slmcore.qt import SLMQtSessionFactory

    uploads = []
    device = SLMDeviceProvider(
        upload_frame=lambda frame:uploads.append(frame.copy()),
    )
    session,panel = SLMQtSessionFactory().create(
        setup=_setup(),
        host_services=SLMHostServices(device=device),
    )
    try:
        assert uploads == []
        session.initialize_device(show_error=False)
        assert len(uploads) == 1
    finally:
        session.dispose()
        panel.deleteLater()


def test_session_factory_cleans_panel_when_session_construction_fails(monkeypatch):
    _app()
    import slmcore.qt.application.factory as factory_module

    deleted = []

    class FakePanel:
        def __init__(self,**_kwargs):
            pass

        def deleteLater(self):
            deleted.append(True)

    def fail_session(**_kwargs):
        raise RuntimeError("session construction failed")

    monkeypatch.setattr(factory_module,"SLMPanel",FakePanel)
    monkeypatch.setattr(factory_module,"SLMQtSession",fail_session)

    factory = factory_module.SLMQtSessionFactory()
    with pytest.raises(RuntimeError,match="session construction failed"):
        factory.create(setup=_setup())
    assert deleted == [True]


def test_session_factory_accepts_custom_registries():
    _app()
    from slmcore.qt import SLMQtSessionFactory
    from slmcore.engine.registry import SLMRegistries

    registries = SLMRegistries()
    factory = SLMQtSessionFactory(registries=registries)
    session,panel = factory.create(setup=_setup())
    try:
        assert session.runtime_factory.registries is registries
    finally:
        session.dispose()
        panel.deleteLater()


def test_slmcore_qt_top_level_is_strict_host_facing_api():
    _app()
    import slmcore.qt as qt

    assert set(qt.__all__) == {
        "DEFAULT_RENDER_POLICY",
        "DEFAULT_RUNTIME_VIEW_INTERACTION_SETTINGS",
        "DEFAULT_SLM_PANEL_LAYOUT_POLICY",
        "PreviewContainer",
        "PreviewPlacement",
        "RenderPolicy",
        "RuntimeViewInteractionSettings",
        "SectionsDisplayMode",
        "SLMPanel",
        "SLMPanelLayoutPolicy",
        "SLMPreviewPanel",
        "SLMPreviewView",
        "SLMQtSession",
        "SLMQtSessionFactory",
        "SLMQtSessionGroup",
        "SLMControlMode",
        "SLMControlModeSelector",
    }
    assert not hasattr(qt,"ParamForm")
    assert not hasattr(qt,"SectionsCollectionView")
    assert not hasattr(qt,"SLMRuntimeViewBinding")
