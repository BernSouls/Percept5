"""[PHASE 2] EVERY EMITTED LENS TYPE IS PARTITIONED.

The old pin compared two HARDCODED literals (V1_TIER | HIGHER_TIER)
against the partition, so a new front-end lens did NOT redden it -- and
the two literals did not even enumerate the higher structural lenses
the front end emits (CONTOUR_PEAK, PEAK_CHAIN, ContourFragment,
Corner, EndStopped, CurveComplex).

THIS pin reads the source of truth: the V1 lens names, the higher lens
names, and the `produces` field of EVERY derived lens declaration.
A lens the front end can emit but the partition does not know is a
missing registration and fails here.
"""
from lenses.base import _LENS_NAMES
from lenses.derived_common import HIGHER_LENS_NAMES, LENS_INPUT_DECLARATIONS
from matching.relation_frame import (ATTRIBUTE_LENS_TYPES,
                                       FRAME_LENS_TYPES,
                                       NON_LENS_TYPES)


def _emitted():
    names = set(_LENS_NAMES) | set(HIGHER_LENS_NAMES)
    for decl in LENS_INPUT_DECLARATIONS:
        produced = getattr(decl, "produces", None)
        if produced:
            names.add(produced)
    return names


def test_every_emitted_lens_type_is_partitioned():
    missing = sorted(_emitted() - (FRAME_LENS_TYPES | ATTRIBUTE_LENS_TYPES
                                      | NON_LENS_TYPES))
    assert not missing, (
        "unregistered emitted lens types: %r -- a new lens must be added"
        " to the FRAME, the ATTRIBUTE or the NON_LENS partition" % (missing,))


def test_the_partition_is_a_partition():
    """No type may be in two partitions, and none may be in none."""
    assert not (FRAME_LENS_TYPES & ATTRIBUTE_LENS_TYPES)
    assert not (FRAME_LENS_TYPES & NON_LENS_TYPES)
    assert not (ATTRIBUTE_LENS_TYPES & NON_LENS_TYPES)


def test_an_unregistered_lens_is_not_silently_a_frame():
    """The partition must be EXPLICIT: an unknown type is neither."""
    from matching.relation_frame import is_frame
    assert not is_frame("A_LENS_THAT_DOES_NOT_EXIST")
    assert "A_LENS_THAT_DOES_NOT_EXIST" not in ATTRIBUTE_LENS_TYPES
