"""Standalone composition root for the slmcore Qt demo."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from slmcore import SLMDefinition
from slmcore.calibration import SLMCalibrationStore
from slmcore.host import MockSLMDeviceProvider,SLMHostServices
from slmcore.qt import (
    PreviewContainer,
    PreviewPlacement,
    SLMPanelLayoutPolicy,
    SLMQtSession,
    SLMQtSessionFactory,
    SLMQtSessionGroup,
)

from .preferences import DemoPreferences
from .setup import DISPLAY_NAMES,create_demo_definitions
from .window import DemoMainWindow


logger = logging.getLogger(__name__)


class DemoHost:
    """Assemble reusable slmcore sessions without any physical hardware."""

    def __init__(self,window: DemoMainWindow,*,data_dir: str | Path) -> None:
        self.window = window
        self.data_dir = Path(data_dir).expanduser().resolve()
        self.data_dir.mkdir(parents=True,exist_ok=True)
        self.preferences = DemoPreferences(self.data_dir)
        self.calibration_store = SLMCalibrationStore(
            self.data_dir / "calibrations",
        )
        self.factory = SLMQtSessionFactory(
            calibration_store=self.calibration_store,
        )
        self.group = SLMQtSessionGroup(parent=window)
        self.sessions: dict[str,SLMQtSession] = {}
        self.devices: dict[str,MockSLMDeviceProvider] = {}
        self._disposed = False

        self.group.sigControlModeChanged.connect(window.set_control_mode)
        self.group.sigControlModeAvailabilityChanged.connect(
            window.set_control_mode_change_enabled,
        )
        window.sigControlModeRequested.connect(self.set_control_mode)

    def initialize(self) -> None:
        """Construct, mount and initialize every demo SLM."""
        for definition in create_demo_definitions():
            self._initialize_slm(definition)
        self.window.set_control_mode(self.group.control_mode)
        self.window.set_control_mode_change_enabled(
            self.group.can_change_control_mode,
        )

    def set_control_mode(self,mode: Any) -> None:
        if not self.group.set_control_mode(mode):
            self.window.set_control_mode(self.group.control_mode)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        for slm_key,session in tuple(self.sessions.items()):
            self.group.remove_session(slm_key)
            self.window.remove_slm(slm_key)
            try:
                session.dispose()
            except Exception:
                logger.exception("Failed to dispose demo session %s",slm_key)
        self.sessions.clear()
        self.devices.clear()

    def _initialize_slm(self,definition: SLMDefinition) -> None:
        slm_key = definition.identity.key
        if slm_key in self.sessions:
            raise KeyError("SLM %r is already initialized" % slm_key)

        device = MockSLMDeviceProvider(requires_explicit_connection=True)
        services = self._host_services(slm_key,device)
        session,panel = self.factory.create(
            definition=definition,
            config_directory=self.data_dir / "configs" / slm_key,
            host_services=services,
            display_name=DISPLAY_NAMES.get(slm_key,slm_key),
            auto_upload_frame=True,
            layout_policy=SLMPanelLayoutPolicy(
                preview_placement=PreviewPlacement.LEFT,
                preview_container=PreviewContainer.PLAIN,
                preview_resizable=True,
                preview_initial_size=350,
                preview_min_size=150,
                highlight_active_section=True,
            ),
        )

        try:
            self.window.add_slm(
                slm_key=slm_key,
                display_name=DISPLAY_NAMES.get(slm_key,slm_key),
                panel=panel,
            )
            self.sessions[slm_key] = session
            self.devices[slm_key] = device
            self.group.add_session(session,key=slm_key)
            self._install_session_logging(slm_key,session,device)
        except Exception:
            self.group.remove_session(slm_key)
            self.window.remove_slm(slm_key)
            self.sessions.pop(slm_key,None)
            self.devices.pop(slm_key,None)
            try:
                session.dispose()
            finally:
                panel.deleteLater()
            raise

        result = session.initialize_device(show_error=False)
        if result is None or not result.connected:
            logger.warning("Mock device initialization failed for %s",slm_key)
        else:
            logger.info("Initialized %s with mock device",slm_key)

    def _host_services(
        self,slm_key: str,device: MockSLMDeviceProvider,
    ) -> SLMHostServices:
        return SLMHostServices.from_callbacks(
            device=device,
            measurement_provider=None,
            get_startup_config=(
                lambda key=slm_key:self.preferences.get_startup_config(key)
            ),
            set_startup_config=(
                lambda value,key=slm_key:
                self.preferences.set_startup_config(key,value)
            ),
            get_default_plane=(
                lambda section,key=slm_key:
                self.preferences.get_default_plane(key,section)
            ),
            set_default_plane=(
                lambda section,value,key=slm_key:
                self.preferences.set_default_plane(key,section,value)
            ),
            get_section_display_mode=(
                lambda key=slm_key:
                self.preferences.get_section_display_mode(key)
            ),
            set_section_display_mode=(
                lambda value,key=slm_key:
                self.preferences.set_section_display_mode(key,value)
            ),
        )

    @staticmethod
    def _install_session_logging(
        slm_key: str,
        session: SLMQtSession,
        device: MockSLMDeviceProvider,
    ) -> None:
        session.sigError.connect(
            lambda title,error,key=slm_key:
                logger.error("[%s] %s: %s",key,title,error)
        )
        session.sigWarning.connect(
            lambda title,message,key=slm_key:
                logger.warning("[%s] %s: %s",key,title,message)
        )
        session.sigInfo.connect(
            lambda title,message,key=slm_key:
                logger.info("[%s] %s: %s",key,title,message)
        )
        session.sigUploadFailed.connect(
            lambda error,key=slm_key:
                logger.error("[%s] frame upload failed: %s",key,error)
        )
        session.sigFrameChanged.connect(
            lambda _frame,key=slm_key,mock=device:
                logger.debug(
                    "[%s] frame published to mock device (upload #%d)",
                    key,mock.upload_count,
                )
        )
