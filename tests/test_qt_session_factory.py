import pytest

from slmcore import DEFAULT_REGISTRIES,SLMGeometry,SLMIdentity
from slmcore.application import SLMDefinition,SLMLayoutPolicy,SLMRuntimeFactory
from slmcore.config import SLMConfigRepository
from slmcore.host import (
    ConfigurationPreferences,SectionViewPreferences,SLMDeviceProvider,
    SLMHostServices,
)
from slmcore.engine.section import SectionSplitLayout,create_split_section_geometries


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


def _setup(tmp_path=None):
    geometry = SLMGeometry(width=24,height=12,pixel_size_um=1.0)
    layout = SectionSplitLayout(n_sections=2,axis="x")
    definition = SLMDefinition(
        identity=SLMIdentity("slm","SER123"),
        geometry=geometry,
        layout_policy=SLMLayoutPolicy(
            customizable=True,
            setup_layout=layout,
            setup_section_geometries=create_split_section_geometries(
                geometry,layout,
            ),
        ),
    )
    repository = (
        None if tmp_path is None
        else SLMConfigRepository(tmp_path,DEFAULT_REGISTRIES)
    )
    return definition,repository


def _runtime(definition,repository=None):
    return SLMRuntimeFactory(
        definition=definition,
        registries=DEFAULT_REGISTRIES,
        config_repository=repository,
    ).create_default()


def test_session_factory_constructs_default_session_and_panel():
    _app()
    from slmcore.qt import SLMPanel,SLMQtSession,SLMQtSessionFactory

    definition,_repository = _setup()
    factory = SLMQtSessionFactory()
    session,panel = factory.create(
        definition=definition,
        display_name="Test SLM",
    )
    try:
        assert isinstance(session,SLMQtSession)
        assert isinstance(panel,SLMPanel)
        assert session.panel is panel
        assert session.runtime_factory.definition is definition
        assert session.runtime_factory.registries is DEFAULT_REGISTRIES
        assert session.config_repository is None
        assert session.current_config_path is None
        assert session.display_name == "Test SLM"
    finally:
        session.dispose()
        panel.deleteLater()


def test_session_factory_uses_startup_config_and_view_preference(tmp_path):
    _app()
    from slmcore.qt import SectionsDisplayMode,SLMQtSessionFactory

    definition,repository = _setup(tmp_path)
    runtime = _runtime(definition,repository)
    repository.save("startup.h5",runtime.create_config(),"startup",overwrite=False)

    services = SLMHostServices(
        configuration_preferences=ConfigurationPreferences(
            get_startup_config=lambda:"startup.h5",
            set_startup_config=lambda _value:None,
        ),
        section_view_preferences=SectionViewPreferences(
            get_display_mode=lambda:"horizontal",
            set_display_mode=lambda _value:None,
        ),
    )
    factory = SLMQtSessionFactory()
    session,panel = factory.create(
        definition=definition,
        config_directory=tmp_path,
        host_services=services,
    )
    try:
        assert session.current_config_path == str(session.config_repository.resolve("startup.h5"))
        assert session.config_repository.directory == tmp_path
        assert session.config_repository.registries is DEFAULT_REGISTRIES
        assert panel.section_host.display_mode == SectionsDisplayMode.HORIZONTAL
    finally:
        session.dispose()
        panel.deleteLater()


def test_session_factory_surfaces_startup_warning():
    _app()
    from slmcore.qt import SLMQtSessionFactory

    definition,_repository = _setup()
    services = SLMHostServices(
        configuration_preferences=ConfigurationPreferences(
            get_startup_config=lambda:"missing.h5",
            set_startup_config=lambda _value:None,
        ),
    )
    session,panel = SLMQtSessionFactory().create(
        definition=definition,host_services=services,
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
    definition,_repository = _setup()
    session,panel = SLMQtSessionFactory().create(
        definition=definition,
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

    definition,_repository = _setup()
    monkeypatch.setattr(factory_module,"SLMPanel",FakePanel)
    monkeypatch.setattr(factory_module,"SLMQtSession",fail_session)

    factory = factory_module.SLMQtSessionFactory()
    with pytest.raises(RuntimeError,match="session construction failed"):
        factory.create(definition=definition)
    assert deleted == [True]


def test_session_factory_accepts_custom_registries():
    _app()
    from slmcore.qt import SLMQtSessionFactory
    from slmcore.engine.registry import SLMRegistries

    definition,_repository = _setup()
    registries = SLMRegistries()
    factory = SLMQtSessionFactory(registries=registries)
    session,panel = factory.create(definition=definition)
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
