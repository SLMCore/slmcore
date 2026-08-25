from __future__ import annotations



from qtpy import QtWidgets

from ...application.definition import SLMDefinition
from ...application.runtime_factory import SLMRuntimeFactory
from ...calibration.store import SLMCalibrationStore
from ...cgh.execution.executor import CGHExecutor
from ...config.repository import SLMConfigRepository
from ...corrections import SLMCorrectionStore
from ...host.services import SLMHostServices
from ...engine.registry import DEFAULT_REGISTRIES,SLMRegistries
from ..panel.panel import SLMPanel
from ..panel.policy import (
    DEFAULT_SLM_PANEL_LAYOUT_POLICY,
    SLMPanelLayoutPolicy,
)
from ..sections.display import SectionsDisplayMode
from ..sections.policy import DEFAULT_RENDER_POLICY,RenderPolicy
from .interaction import (
    DEFAULT_RUNTIME_VIEW_INTERACTION_SETTINGS,
    RuntimeViewInteractionSettings,
)
from .session import SLMQtSession


class SLMQtSessionFactory:
    """Construct the standard reusable Qt session and panel for one SLM.

    The factory owns the generic runtime/startup/panel/session assembly. Hosts
    provide the physical SLM definition, optional stores, and host capabilities.
    It does not initialize or connect the physical device; hosts should do that
    only after successfully mounting/registering the returned objects.
    """

    def __init__(
        self,
        *,
        registries: SLMRegistries | None=None,
        calibration_store: SLMCalibrationStore | None=None,
    ) -> None:
        registries = DEFAULT_REGISTRIES if registries is None else registries
        if not isinstance(registries,SLMRegistries):
            raise TypeError("registries must be SLMRegistries or None")
        if (
            calibration_store is not None
            and not isinstance(calibration_store,SLMCalibrationStore)
        ):
            raise TypeError("calibration_store must be an SLMCalibrationStore or None")

        self.registries = registries
        self.calibration_store = calibration_store

    def create(
        self,
        *,
        definition: SLMDefinition,
        correction_store: SLMCorrectionStore | None=None,
        config_directory: object | None=None,
        host_services: SLMHostServices | None=None,
        display_name: str="",
        interaction_settings: RuntimeViewInteractionSettings=(
            DEFAULT_RUNTIME_VIEW_INTERACTION_SETTINGS
        ),
        layout_policy: SLMPanelLayoutPolicy=DEFAULT_SLM_PANEL_LAYOUT_POLICY,
        render_policy: RenderPolicy=DEFAULT_RENDER_POLICY,
        cgh_executor: CGHExecutor | None=None,
        auto_upload_frame: bool=True,
        parent: QtWidgets.QWidget | None=None,
    ) -> tuple[SLMQtSession, SLMPanel]:
        if not isinstance(definition,SLMDefinition):
            raise TypeError("definition must be an SLMDefinition")
        if (
            correction_store is not None
            and not isinstance(correction_store,SLMCorrectionStore)
        ):
            raise TypeError(
                "correction_store must be an SLMCorrectionStore or None"
            )
        services = host_services or SLMHostServices()
        config_repository = (
            None
            if config_directory is None
            else SLMConfigRepository(config_directory,self.registries)
        )
        runtime_factory = SLMRuntimeFactory(
            definition=definition,
            registries=self.registries,
            correction_store=correction_store,
            config_repository=config_repository,
        )
        startup_name = None
        if services.configuration_preferences is not None:
            startup_name = services.configuration_preferences.get()
        startup = runtime_factory.create_startup(startup_name)
        display_mode = self._display_mode(services)

        panel = None
        session = None
        try:
            panel = SLMPanel(
                section_snapshots=startup.runtime.get_section_snapshots(),
                initial_frame=startup.runtime.artifacts.eightbit,
                current_config_path=startup.config_path,
                section_display_mode=display_mode,
                render_policy=render_policy,
                layout_policy=layout_policy,
                parent=parent,
            )
            session = SLMQtSession(
                runtime=startup.runtime,
                panel=panel,
                host_services=services,
                interaction_settings=interaction_settings,
                cgh_executor=cgh_executor,
                auto_upload_frame=auto_upload_frame,
                display_name=display_name,
                calibration_store=self.calibration_store,
                apply_startup_calibration_defaults=(startup.config_path is None),
                runtime_factory=runtime_factory,
                config_repository=config_repository,
                current_config_path=startup.config_path,
                parent=panel,
            )
            if startup.warnings:
                panel.set_status("; ".join(startup.warnings),error=True)
            return session,panel
        except Exception:
            if session is not None:
                try:
                    session.dispose()
                except Exception:
                    pass
            if panel is not None:
                panel.deleteLater()
            raise

    @staticmethod
    def _display_mode(host_services: SLMHostServices) -> SectionsDisplayMode:
        preferences = host_services.section_view_preferences
        if preferences is None:
            return SectionsDisplayMode.TABS
        value = preferences.get()
        if not value:
            return SectionsDisplayMode.TABS
        try:
            return SectionsDisplayMode.normalize(value)
        except ValueError:
            return SectionsDisplayMode.TABS


__all__ = ["SLMQtSessionFactory"]
