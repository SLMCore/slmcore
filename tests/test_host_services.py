import numpy as np
import pytest

from slmcore.host import (
    DeviceConnectionResult,MockSLMDeviceProvider,SLMDeviceProvider,SLMHostServices,
)


def test_host_services_device_upload_is_an_optional_capability():
    frame = np.zeros((4,5),dtype=np.uint8)
    received = []
    device = SLMDeviceProvider(
        upload_frame=lambda value:received.append(value),
    )
    services = SLMHostServices(device=device)

    services.upload(frame)

    assert received == [frame]
    SLMHostServices().upload(frame)


def test_host_services_rejects_invalid_device_capability():
    with pytest.raises(TypeError,match="device"):
        SLMHostServices(device=object())


def test_device_provider_requires_connection_callbacks_when_requested():
    with pytest.raises(ValueError,match="connect and disconnect"):
        SLMDeviceProvider(
            upload_frame=lambda _frame:None,
            requires_explicit_connection=True,
        )


def test_device_provider_normalizes_legacy_connection_tuples():
    provider = SLMDeviceProvider(
        upload_frame=lambda _frame:None,
        connect=lambda:(True,"SER123"),
        disconnect=lambda:(True,"closed"),
        requires_explicit_connection=True,
    )

    connected = provider.connect()
    disconnected = provider.disconnect()

    assert connected == DeviceConnectionResult(
        connected=True,device_info="SER123",
    )
    assert disconnected == DeviceConnectionResult(
        connected=False,message="closed",
    )


def test_mock_device_provider_retains_uploaded_frame():
    provider = MockSLMDeviceProvider(requires_explicit_connection=True)
    frame = np.arange(12,dtype=np.uint8).reshape(3,4)

    assert provider.is_mock
    assert provider.requires_explicit_connection
    assert not provider.connected
    assert provider.connect().connected
    provider.upload_frame(frame)
    assert provider.upload_count == 1
    np.testing.assert_array_equal(provider.last_frame,frame)
    assert not provider.disconnect().connected


class _MeasurementProvider:
    def available_sources(self,section_key):
        return ("camera",)

    def preferred_source(self,section_key,available):
        return available[0]

    def acquire(self,section_key,source,*,metadata,on_result,on_error):
        return None


def test_host_services_accepts_measurement_provider_capability():
    provider = _MeasurementProvider()
    services = SLMHostServices(measurement_provider=provider)

    assert services.measurement_provider is provider
    assert services.can_upload_frame is False


def test_host_services_rejects_incomplete_measurement_provider():
    class Incomplete:
        def available_sources(self,section_key):
            return ()

    with pytest.raises(TypeError,match="measurement_provider"):
        SLMHostServices(measurement_provider=Incomplete())


def test_host_services_accepts_calibration_preferences_capability():
    from slmcore.host import CalibrationPreferences

    preferences = CalibrationPreferences(
        get_default_plane=lambda _key:None,
        set_default_plane=lambda _key,_value:None,
    )
    services = SLMHostServices(calibration_preferences=preferences)
    assert services.calibration_preferences is preferences


def test_host_services_rejects_invalid_calibration_preferences():
    with pytest.raises(TypeError,match="calibration_preferences"):
        SLMHostServices(calibration_preferences=object())


def test_host_services_accepts_configuration_and_view_preferences():
    from slmcore.host import ConfigurationPreferences,SectionViewPreferences

    startup = {"value":"default.h5"}
    display = {"value":"tabs"}
    configuration = ConfigurationPreferences(
        get_startup_config=lambda:startup["value"],
        set_startup_config=lambda value:startup.__setitem__("value",value),
    )
    view = SectionViewPreferences(
        get_display_mode=lambda:display["value"],
        set_display_mode=lambda value:display.__setitem__("value",value),
    )
    services = SLMHostServices(
        configuration_preferences=configuration,
        section_view_preferences=view,
    )

    assert services.configuration_preferences.get() == "default.h5"
    services.configuration_preferences.set(None)
    assert startup["value"] is None
    assert services.section_view_preferences.get() == "tabs"
    services.section_view_preferences.set("horizontal")
    assert display["value"] == "horizontal"


def test_host_services_from_callbacks_builds_preference_capabilities():
    startup = {"value":"startup.h5"}
    plane = {"sec_0":"sample"}
    display = {"value":"tabs"}

    services = SLMHostServices.from_callbacks(
        get_startup_config=lambda:startup["value"],
        set_startup_config=lambda value:startup.__setitem__("value",value),
        get_default_plane=lambda section:plane.get(section),
        set_default_plane=lambda section,value:plane.__setitem__(section,value),
        get_section_display_mode=lambda:display["value"],
        set_section_display_mode=lambda value:display.__setitem__("value",value),
    )

    assert services.configuration_preferences.get() == "startup.h5"
    services.configuration_preferences.set(None)
    assert startup["value"] is None
    assert services.calibration_preferences.get("sec_0") == "sample"
    services.calibration_preferences.set("sec_0","camera")
    assert plane["sec_0"] == "camera"
    assert services.section_view_preferences.get() == "tabs"
    services.section_view_preferences.set("horizontal")
    assert display["value"] == "horizontal"


def test_host_services_from_callbacks_requires_complete_preference_pairs():
    with pytest.raises(TypeError,match="startup config"):
        SLMHostServices.from_callbacks(get_startup_config=lambda:None)
    with pytest.raises(TypeError,match="default plane"):
        SLMHostServices.from_callbacks(set_default_plane=lambda _section,_value:None)
    with pytest.raises(TypeError,match="section display mode"):
        SLMHostServices.from_callbacks(get_section_display_mode=lambda:"tabs")


def test_host_services_with_fallbacks_only_fills_missing_capabilities():
    from slmcore.host import ConfigurationPreferences,SectionViewPreferences

    explicit_view = SectionViewPreferences(
        get_display_mode=lambda:"horizontal",
        set_display_mode=lambda _value:None,
    )
    fallback_config = ConfigurationPreferences(
        get_startup_config=lambda:"startup.h5",
        set_startup_config=lambda _value:None,
    )
    fallback_view = SectionViewPreferences(
        get_display_mode=lambda:"tabs",
        set_display_mode=lambda _value:None,
    )
    services = SLMHostServices(
        section_view_preferences=explicit_view,
    ).with_fallbacks(
        SLMHostServices(
            configuration_preferences=fallback_config,
            section_view_preferences=fallback_view,
        )
    )

    assert services.configuration_preferences is fallback_config
    assert services.section_view_preferences is explicit_view
