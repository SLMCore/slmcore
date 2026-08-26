"""Canonical SLM setups used by the standalone Qt demo."""

from slmcore import (
    SLMGeometry,
    SLMIdentity,
    SLMSectionsSetup,
    SLMSetup,
    SectionSplitLayout,
)


DISPLAY_NAMES = {
    "demo_slm_1":"Demo SLM 1 — Single section",
    "demo_slm_2":"Demo SLM 2 — Two sections",
}


def create_demo_setups() -> tuple[SLMSetup,...]:
    """Return two hardware-free setups that exercise common layouts."""
    return (
        _setup(
            key="demo_slm_1",
            serial_number="DEMO-001",
            width=512,
            height=512,
            pixel_size_um=8.0,
            layout=SectionSplitLayout(n_sections=1,axis="x"),
            customizable=False,
        ),
        _setup(
            key="demo_slm_2",
            serial_number="DEMO-002",
            width=512,
            height=256,
            pixel_size_um=8.0,
            layout=SectionSplitLayout(n_sections=2,axis="x"),
            customizable=True,
        ),
    )


def _setup(
    *,
    key: str,
    serial_number: str,
    width: int,
    height: int,
    pixel_size_um: float,
    layout: SectionSplitLayout,
    customizable: bool,
) -> SLMSetup:
    return SLMSetup(
        identity=SLMIdentity(key,serial_number),
        geometry=SLMGeometry(
            width=width,
            height=height,
            pixel_size_um=pixel_size_um,
        ),
        sections=SLMSectionsSetup(
            layout=layout,
            customizable=customizable,
        ),
    )
