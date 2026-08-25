from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from ..engine.section.geometry import (
    SectionGeometry,SectionSplitLayout,validate_config_section_layout,
)
from ..engine.device import SLMGeometry,SLMIdentity


@dataclass(frozen=True)
class SLMLayoutPolicy:
    """Setup-level constraints for the config-level section layout."""

    customizable: bool
    setup_layout: SectionSplitLayout
    setup_section_geometries: Mapping[str,SectionGeometry]

    def __post_init__(self) -> None:
        sections = dict(self.setup_section_geometries)
        if len(sections) != self.setup_layout.n_sections:
            raise ValueError(
                "setup section geometry count must match setup_layout.n_sections"
            )
        object.__setattr__(
            self,"setup_section_geometries",MappingProxyType(sections),
        )

    @property
    def section_count(self) -> int:
        return len(self.setup_section_geometries)

    def validate(
        self,
        physical_geometry: SLMGeometry,
        config_geometry: SLMGeometry,
        section_geometries: Mapping[str,SectionGeometry],
    ):
        if len(section_geometries) != self.section_count:
            raise ValueError("Changing section count is not supported")
        return validate_config_section_layout(
            physical_geometry=physical_geometry,
            config_geometry=config_geometry,
            config_section_geometries=section_geometries,
            setup_section_geometries=self.setup_section_geometries,
            section_layout_customizable=self.customizable,
        )


@dataclass(frozen=True)
class SLMDefinition:
    """Host-supplied physical identity and immutable layout constraints."""

    identity: SLMIdentity
    geometry: SLMGeometry
    layout_policy: SLMLayoutPolicy
