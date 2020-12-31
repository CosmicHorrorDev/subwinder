from hypothesis import given
from hypothesis.strategies import binary

from dev.pack_subtitles.pack_subtitles import pack
from subwinder.utils import extract


# Compressing results in a different timestamp so our best bet is to test the full
# cycle using random data
@given(binary())
def test_pack_then_extract(bytes):
    assert extract(pack(bytes)) == bytes
