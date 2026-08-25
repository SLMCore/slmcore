"""Canonical SLM definitions used by the standalone Qt demo."""

from slmcore import (
    SLMGeometry,
    SLMIdentity,
    SectionSplitLayout,
    create_split_section_geometries,
)
from slmcore.application import SLMDefinition,SLMLayoutPolicy


DISPLAY_NAMES = {
    "demo_slm_1":"Demo SLM 1 — Single section",
    "demo_slm_2":"Demo SLM 2 — Two sections",
}


def create_demo_definitions() -> tuple[SLMDefinition,...]:
    """Return two hardware-free definitions that exercise common layouts."""
    return (
        _definition(
            key="demo_slm_1",
            serial_number="DEMO-001",
            width=512,
            height=512,
            pixel_size_um=8.0,
            layout=SectionSplitLayout(n_sections=1,axis="x"),
            customizable=False,
        ),
        _definition(
            key="demo_slm_2",
            serial_number="DEMO-002",
            width=512,
            height=256,
            pixel_size_um=8.0,
            layout=SectionSplitLayout(n_sections=2,axis="x"),
            customizable=True,
        ),
    )


def _definition(
    *,
    key: str,
    serial_number: str,
    width: int,
    height: int,
    pixel_size_um: float,
    layout: SectionSplitLayout,
    customizable: bool,
) -> SLMDefinition:
    geometry = SLMGeometry(
        width=width,
        height=height,
        pixel_size_um=pixel_size_um,
    )
    return SLMDefinition(
        identity=SLMIdentity(key,serial_number),
        geometry=geometry,
        layout_policy=SLMLayoutPolicy(
            customizable=customizable,
            setup_layout=layout,
            setup_section_geometries=create_split_section_geometries(
                geometry,layout,
            ),
        ),
    )
