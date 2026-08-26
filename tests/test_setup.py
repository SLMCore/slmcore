import pytest

from slmcore import (
    SLMCorrectionSetup,
    SLMGeometry,
    SLMHardwareSetup,
    SLMIdentity,
    SLMSectionsSetup,
    SLMSetup,
    SectionSplitLayout,
)


def _setup():
    return SLMSetup(
        identity=SLMIdentity("pupil_slm","SER-001"),
        geometry=SLMGeometry(width=10,height=6,pixel_size_um=8.0),
        sections=SLMSectionsSetup(
            layout=SectionSplitLayout(n_sections=2,axis="x"),
            customizable=True,
        ),
        corrections=SLMCorrectionSetup(
            wavelength_table_file="wavelength.json",
            preferred_directory="external/corrections",
        ),
        hardware=SLMHardwareSetup(
            driver="example",
            options={"device_index":0},
        ),
    )


def test_identity_requires_stable_serial_number():
    with pytest.raises(ValueError,match="serial_number"):
        SLMIdentity("slm","")
    with pytest.raises(ValueError,match="serial_number"):
        SLMIdentity("slm",None)


def test_setup_derives_section_geometry_from_canonical_layout():
    setup = _setup()
    assert tuple(setup.section_geometries) == ("sec_0","sec_1")
    assert setup.section_geometries["sec_0"].width == 5
    assert setup.section_geometries["sec_1"].x == 5
    assert setup.section_count == 2


def test_setup_roundtrips_through_dict():
    setup = _setup()
    restored = SLMSetup.from_dict(setup.to_dict())
    assert restored == setup
    assert dict(restored.hardware.options) == {"device_index":0}
    assert restored.section_geometries == setup.section_geometries
