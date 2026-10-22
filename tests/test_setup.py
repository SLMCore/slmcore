import json

import pytest

from slmcore import (
    SLMDefinition,
    SLMGeometry,
    SLMHardwareConfig,
    SLMIdentity,
    SLMSectionsDefinition,
    SLMStartupPreferences,
    SectionSplitLayout,
    load_slm_setup_file,
    save_slm_startup_preferences,
)


def _definition():
    return SLMDefinition(
        identity=SLMIdentity("pupil_slm","SER-001","Pupil SLM"),
        geometry=SLMGeometry(width=10,height=6,pixel_size_um=8.0),
        sections=SLMSectionsDefinition(
            layout=SectionSplitLayout(n_sections=2,axis="x"),
            customizable=True,
        ),
    )


def _hardware():
    return SLMHardwareConfig(
        driver="example",
        options={"device_index":0},
    )


def test_identity_requires_stable_serial_number():
    with pytest.raises(ValueError,match="serial_number"):
        SLMIdentity("slm","")
    with pytest.raises(ValueError,match="serial_number"):
        SLMIdentity("slm",None)


def test_display_name_is_non_identifying():
    assert SLMIdentity("slm","SER","First") == SLMIdentity("slm","SER","Renamed")


def test_definition_derives_section_geometry_from_canonical_layout():
    definition = _definition()
    assert tuple(definition.section_geometries) == ("sec_0","sec_1")
    assert definition.section_geometries["sec_0"].width == 5
    assert definition.section_geometries["sec_1"].x == 5
    assert definition.section_count == 2


def test_definition_roundtrips_through_dict_without_hardware():
    definition = _definition()
    restored = SLMDefinition.from_dict(definition.to_dict())
    assert restored == definition
    assert restored.identity.display_name == "Pupil SLM"
    assert restored.section_geometries == definition.section_geometries
    assert "hardware" not in definition.to_dict()


def test_definition_from_dict_allows_host_key_override():
    data = _definition().to_dict()
    data["identity"].pop("key")
    restored = SLMDefinition.from_dict(data,key="imswitch_key")
    assert restored.identity.key == "imswitch_key"
    assert restored.identity.serial_number == "SER-001"


def test_hardware_config_roundtrips_independently():
    hardware = _hardware()
    restored = SLMHardwareConfig.from_dict(hardware.to_dict())
    assert restored == hardware
    assert dict(restored.options) == {"device_index":0}
    assert SLMHardwareConfig.from_dict(None) is None


def test_startup_preferences_roundtrip():
    preferences = SLMStartupPreferences(
        startup_config="default.h5",
        default_mappings={"sec_0":"Sample"},
        section_display_mode="horizontal",
    )
    assert SLMStartupPreferences.from_dict(preferences.to_dict()) == preferences


def test_canonical_setup_file_load_and_preference_update(tmp_path):
    path = tmp_path / "slm.json"
    definition = _definition()
    hardware = _hardware()
    path.write_text(json.dumps({
        "schema_version":1,
        "definition":definition.to_dict(),
        "hardware":hardware.to_dict(),
        "startup_preferences":{
            "startup_config":None,
            "default_mappings":{},
            "section_display_mode":"tabs",
        },
        "host_note":"preserved",
    }),encoding="utf-8")

    restored_definition,restored_hardware,preferences = load_slm_setup_file(path)
    assert restored_definition == definition
    assert restored_hardware == hardware
    assert preferences == SLMStartupPreferences()

    changed = SLMStartupPreferences(
        startup_config="startup.h5",
        default_mappings={"sec_0":"Sample"},
        section_display_mode="horizontal",
    )
    save_slm_startup_preferences(path,changed)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["definition"] == definition.to_dict()
    assert data["hardware"] == hardware.to_dict()
    assert data["startup_preferences"] == changed.to_dict()
    assert data["host_note"] == "preserved"

def test_definition_authoring_schema_describes_canonical_fields():
    from slmcore import slm_definition_schema

    schema = slm_definition_schema()
    assert schema["$schema"].endswith("2020-12/schema")
    assert schema["properties"]["geometry"]["properties"]["width"]["minimum"] == 1
    layout = schema["properties"]["sections"]["properties"]["layout"]
    assert layout["properties"]["axis"]["enum"] == ["x","y"]
    assert layout["properties"]["mode"]["enum"] == ["even","manual"]
    assert "key" in schema["properties"]["identity"]["required"]
    serialized = _definition().to_dict()
    assert set(schema["properties"]) == set(serialized)
    assert set(schema["properties"]["identity"]["properties"]) == set(serialized["identity"])
    assert set(schema["properties"]["geometry"]["properties"]) == set(serialized["geometry"])
    assert set(schema["properties"]["sections"]["properties"]) == set(serialized["sections"])
    assert set(layout["properties"]) == set(serialized["sections"]["layout"])


def test_definition_authoring_schema_supports_host_managed_key():
    from slmcore import slm_definition_schema

    schema = slm_definition_schema(host_managed_key=True)
    identity = schema["properties"]["identity"]
    assert "key" not in identity["properties"]
    assert "key" not in identity["required"]
    assert "serial_number" in identity["required"]


def test_authoring_schemas_are_isolated_mutable_copies():
    from slmcore import slm_definition_schema,slm_startup_preferences_schema

    definition = slm_definition_schema()
    definition["properties"]["geometry"]["title"] = "changed"
    assert slm_definition_schema()["properties"]["geometry"]["title"] == "Geometry"

    preferences = slm_startup_preferences_schema()
    preferences["properties"]["startup_config"]["title"] = "changed"
    assert (
        slm_startup_preferences_schema()["properties"]["startup_config"]["title"]
        == "Startup config"
    )


def test_startup_preferences_authoring_schema_covers_current_preferences():
    from slmcore import slm_startup_preferences_schema

    schema = slm_startup_preferences_schema()
    assert set(schema["properties"]) == set(SLMStartupPreferences().to_dict())
    assert schema["properties"]["section_display_mode"]["enum"] == [
        "tabs","horizontal",
    ]
    orientation = (
        schema["properties"]["feedback_orientations"]
        ["additionalProperties"]["properties"]["default"]
    )
    assert "identity" in orientation["enum"]
    assert "transpose" in orientation["enum"]


def test_authoring_validation_helpers_use_canonical_models():
    from slmcore import validate_slm_definition,validate_slm_startup_preferences

    data = _definition().to_dict()
    data["identity"].pop("key")
    validated = validate_slm_definition(data,key="host_key")
    assert validated.identity.key == "host_key"

    with pytest.raises(ValueError,match="expected 10"):
        invalid = _definition().to_dict()
        invalid["sections"]["layout"].update(
            {"mode":"manual","sizes":[4,4]},
        )
        validate_slm_definition(invalid)

    preferences = validate_slm_startup_preferences({
        "default_mappings":{"sec_0":"Sample"},
    })
    assert preferences.default_mappings["sec_0"] == "Sample"
