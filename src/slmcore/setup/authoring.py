"""Toolkit-independent authoring metadata for canonical SLM setup values.

The schemas in this module are intended for hosts that want to build structured
configuration editors without duplicating slmcore's setup model.  They provide
JSON-Schema-compatible field metadata (types, defaults, descriptions and enums)
for the portable SLM definition and startup preferences.

Schema validation is deliberately not the semantic authority.  Cross-field and
runtime constraints (for example manual section sizes covering the complete SLM)
remain owned by :class:`SLMDefinition` and :class:`SLMStartupPreferences`; hosts
should call the validation helpers here before committing edited values.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any,Mapping

from ..core.cgh.feedback.orientation import FeedbackOrientation
from .model import SLMDefinition
from .preferences import SLMStartupPreferences


_JSON_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"


def _non_empty_string_schema(*,title: str,description: str) -> dict[str,Any]:
    return {
        "type":"string",
        "minLength":1,
        "title":title,
        "description":description,
    }


def _definition_schema() -> dict[str,Any]:
    return {
        "$schema":_JSON_SCHEMA_DRAFT,
        "title":"SLM definition",
        "description":(
            "Portable physical SLM definition owned by slmcore. Hardware binding "
            "and startup/session preferences are separate concerns."
        ),
        "type":"object",
        "properties":{
            "identity":{
                "type":"object",
                "title":"Identity",
                "description":"Stable identity and user-facing name of the physical SLM.",
                "properties":{
                    "key":_non_empty_string_schema(
                        title="Key",
                        description=(
                            "Host/session key used to address this SLM. A host may supply "
                            "this key externally instead of storing it in the definition."
                        ),
                    ),
                    "serial_number":_non_empty_string_schema(
                        title="Serial number",
                        description=(
                            "Stable physical serial number used to identify persistent "
                            "SLM resources."
                        ),
                    ),
                    "display_name":{
                        "type":["string","null"],
                        "title":"Display name",
                        "description":"Optional human-readable SLM name.",
                        "default":None,
                    },
                },
                "required":["key","serial_number"],
                "additionalProperties":True,
            },
            "geometry":{
                "type":"object",
                "title":"Geometry",
                "description":"Physical pixel geometry of the SLM.",
                "properties":{
                    "width":{
                        "type":"integer",
                        "minimum":1,
                        "title":"Width",
                        "description":"Physical SLM width in pixels.",
                    },
                    "height":{
                        "type":"integer",
                        "minimum":1,
                        "title":"Height",
                        "description":"Physical SLM height in pixels.",
                    },
                    "pixel_size_um":{
                        "type":"number",
                        "exclusiveMinimum":0,
                        "title":"Pixel pitch",
                        "description":"Physical SLM pixel pitch in micrometres.",
                    },
                },
                "required":["width","height","pixel_size_um"],
                "additionalProperties":True,
            },
            "sections":{
                "type":"object",
                "title":"Sections",
                "description":"Definition-level fixed-count section layout.",
                "properties":{
                    "layout":{
                        "type":"object",
                        "title":"Layout",
                        "properties":{
                            "n_sections":{
                                "type":"integer",
                                "minimum":1,
                                "title":"Number of sections",
                                "description":"Number of contiguous sections on this SLM.",
                            },
                            "axis":{
                                "type":"string",
                                "enum":["x","y"],
                                "default":"x",
                                "title":"Split axis",
                                "description":"Axis along which the physical SLM is split.",
                            },
                            "mode":{
                                "type":"string",
                                "enum":["even","manual"],
                                "default":"even",
                                "title":"Layout mode",
                                "description":(
                                    "Even divides the selected axis automatically; manual "
                                    "uses the explicit section sizes."
                                ),
                            },
                            "sizes":{
                                "oneOf":[
                                    {"type":"null"},
                                    {
                                        "type":"array",
                                        "items":{"type":"integer","minimum":1},
                                        "minItems":1,
                                    },
                                ],
                                "default":None,
                                "title":"Section sizes",
                                "description":(
                                    "Section sizes in pixels along the split axis. Required "
                                    "for manual layout; semantic validation checks count and "
                                    "full-SLM coverage."
                                ),
                            },
                            "key_prefix":{
                                "type":"string",
                                "minLength":1,
                                "default":"sec_",
                                "title":"Section key prefix",
                                "description":"Prefix used when deriving section keys.",
                            },
                        },
                        "required":["n_sections"],
                        "additionalProperties":True,
                        "allOf":[
                            {
                                "if":{
                                    "properties":{"mode":{"const":"manual"}},
                                    "required":["mode"],
                                },
                                "then":{
                                    "properties":{
                                        "sizes":{
                                            "type":"array",
                                            "items":{"type":"integer","minimum":1},
                                            "minItems":1,
                                        },
                                    },
                                    "required":["sizes"],
                                },
                            },
                        ],
                    },
                    "customizable":{
                        "type":"boolean",
                        "default":False,
                        "title":"Customizable layout",
                        "description":(
                            "Allow saved SLM configs to change section geometry while "
                            "preserving the definition-defined section count."
                        ),
                    },
                },
                "required":["layout"],
                "additionalProperties":True,
            },
        },
        "required":["identity","geometry","sections"],
        "additionalProperties":True,
    }


def _orientation_schema() -> dict[str,Any]:
    return {
        "type":"string",
        "enum":[orientation.value for orientation in FeedbackOrientation],
        "default":FeedbackOrientation.IDENTITY.value,
    }


def _startup_preferences_schema() -> dict[str,Any]:
    orientation = _orientation_schema()
    return {
        "$schema":_JSON_SCHEMA_DRAFT,
        "title":"SLM startup preferences",
        "description":(
            "Persistent defaults applied when constructing an SLM session. These are "
            "preferences rather than physical SLM definition fields."
        ),
        "type":"object",
        "properties":{
            "startup_config":{
                "type":["string","null"],
                "title":"Startup config",
                "description":"Optional saved SLM config loaded when the session starts.",
                "default":None,
            },
            "default_mappings":{
                "type":"object",
                "title":"Default mappings",
                "description":"Default mapping name for each section key.",
                "default":{},
                "additionalProperties":{
                    "type":"string",
                    "minLength":1,
                    "description":"Mapping name.",
                },
            },
            "section_display_mode":{
                "type":"string",
                "enum":["tabs","horizontal"],
                "title":"Section display mode",
                "description":(
                    "Preferred host presentation mode for SLM sections. slmcore stores "
                    "this as a host-facing string; current Qt hosts use 'tabs' or "
                    "'horizontal'."
                ),
                "default":"tabs",
            },
            "feedback_orientations":{
                "type":"object",
                "title":"Feedback orientations",
                "description":"Camera-to-target feedback orientation defaults by section.",
                "default":{},
                "additionalProperties":{
                    "type":"object",
                    "properties":{
                        "default":{
                            **orientation,
                            "title":"Default orientation",
                            "description":"Default feedback orientation for this section.",
                        },
                        "planes":{
                            "type":"object",
                            "title":"Observation-plane overrides",
                            "description":(
                                "Feedback orientation overrides keyed by observation-plane name."
                            ),
                            "default":{},
                            "additionalProperties":{
                                **orientation,
                                "description":"Feedback orientation for this observation plane.",
                            },
                        },
                    },
                    "additionalProperties":True,
                },
            },
            "fov_mapping_corrections":{
                "type":"object",
                "title":"Default FOV corrections",
                "description":"Default FOV-correction selections by section and mapping.",
                "default":{},
                "additionalProperties":{
                    "type":"object",
                    "properties":{
                        "mappings":{
                            "type":"object",
                            "title":"Mapping corrections",
                            "description":"Correction name keyed by mapping name.",
                            "default":{},
                            "additionalProperties":{
                                "type":"string",
                                "minLength":1,
                                "description":"FOV correction name.",
                            },
                        },
                    },
                    "additionalProperties":True,
                },
            },
            "focused_editing":{
                "type":"object",
                "title":"Focused editing",
                "description":"Persistent focused-editor visibility selections by section.",
                "default":{},
                "additionalProperties":{
                    "type":"object",
                    "properties":{
                        "groups":{
                            "type":"array",
                            "title":"Groups",
                            "description":"Group keys rendered atomically in Focused editing.",
                            "items":{"type":"string","minLength":1},
                            "default":[],
                            "uniqueItems":True,
                        },
                        "items":{
                            "type":"object",
                            "title":"Items",
                            "description":(
                                "Selected registry-backed item keys, grouped by editor group key."
                            ),
                            "default":{},
                            "additionalProperties":{
                                "type":"array",
                                "items":{"type":"string","minLength":1},
                                "uniqueItems":True,
                            },
                        },
                    },
                    "additionalProperties":True,
                },
            },
        },
        "additionalProperties":True,
    }


_DEFINITION_SCHEMA = _definition_schema()
_STARTUP_PREFERENCES_SCHEMA = _startup_preferences_schema()


def slm_definition_schema(*,host_managed_key: bool=False) -> dict[str,Any]:
    """Return JSON-Schema-compatible authoring metadata for ``SLMDefinition``.

    ``host_managed_key=True`` describes the payload accepted when the host owns
    the SLM addressing key and passes it separately to :meth:`SLMDefinition.from_dict`.
    In that mode ``identity.key`` is intentionally omitted from the editable
    properties and is not required.

    A fresh deep copy is returned on every call so editor-side annotation cannot
    mutate slmcore's canonical metadata.
    """
    schema = deepcopy(_DEFINITION_SCHEMA)
    if host_managed_key:
        identity = schema["properties"]["identity"]
        identity["properties"].pop("key",None)
        identity["required"] = [
            field for field in identity.get("required",[]) if field != "key"
        ]
    return schema


def slm_startup_preferences_schema() -> dict[str,Any]:
    """Return JSON-Schema-compatible authoring metadata for startup preferences."""
    return deepcopy(_STARTUP_PREFERENCES_SCHEMA)


def validate_slm_definition(
    data: Mapping[str,Any],*,key: str | None=None,
) -> SLMDefinition:
    """Validate authoring data with slmcore's authoritative definition model."""
    return SLMDefinition.from_dict(data,key=key)


def validate_slm_startup_preferences(
    data: Mapping[str,Any] | None,
) -> SLMStartupPreferences:
    """Validate authoring data with slmcore's authoritative preference model."""
    return SLMStartupPreferences.from_dict(data)


__all__ = [
    "slm_definition_schema",
    "slm_startup_preferences_schema",
    "validate_slm_definition",
    "validate_slm_startup_preferences",
]
