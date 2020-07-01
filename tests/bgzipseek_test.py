import io
import os
import os.path

import pytest

from bgzipseek import BGZipSeek


@pytest.fixture
def test_txt():
    pth = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "test_200.txt"
    )
    return open(pth, "rb")


@pytest.fixture
def test_blockgz():
    pth = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "test_200.txt.gz"
    )
    return open(pth, "rb")


class TestBGZipSeek:
    def test_basic(self, test_txt, test_blockgz):
        content = test_txt.read()
        blockgzip = BGZipSeek(test_blockgz)
        # read the whole thing
        print(len(content))
        print(blockgzip.size)
        assert len(content) == blockgzip.size
        # assert content == blockgzip.read()

    def test_seek(self, test_txt, test_blockgz):
        content = test_txt.read()
        blockgzip = BGZipSeek(test_blockgz)

        # read the first X bytes
        assert 0 == blockgzip.tell()
        assert content[:16] == blockgzip.read(16)
        assert 16 == blockgzip.tell()

        # seek back to the start implicit
        blockgzip.seek(0)
        assert 0 == blockgzip.tell()
        assert content[:16] == blockgzip.read(16)
        assert 16 == blockgzip.tell()

        # seek back to the start explicit
        blockgzip.seek(0, io.SEEK_SET)
        assert 0 == blockgzip.tell()
        assert content[:16] == blockgzip.read(16)
        assert 16 == blockgzip.tell()

        # relative seek forward
        blockgzip.seek(16, io.SEEK_CUR)
        assert 32 == blockgzip.tell()
        assert content[32:48] == blockgzip.read(16)
        assert 48 == blockgzip.tell()

        # relative seek backward
        blockgzip.seek(-16, io.SEEK_CUR)
        assert 32 == blockgzip.tell()
        assert content[32:48] == blockgzip.read(16)
        assert 48 == blockgzip.tell()
        # relative seek end
        blockgzip.seek(-16, io.SEEK_END)
        assert len(content) - 16 == blockgzip.tell()
        assert content[-16:] == blockgzip.read(16)
        assert len(content) == blockgzip.tell()

        # seek outside of file
        blockgzip.seek(0)
        with pytest.raises(OSError):
            blockgzip.seek(-len(content) - 1, io.SEEK_CUR)
        with pytest.raises(OSError):
            blockgzip.seek(-len(content) - 1, io.SEEK_END)
        with pytest.raises(OSError):
            blockgzip.seek(-1, io.SEEK_SET)
        with pytest.raises(OSError):
            blockgzip.seek(-1)

    def test_block_boundary(self, test_txt, test_blockgz):
        content = test_txt.read()
        blockgzip = BGZipSeek(test_blockgz)
        blockgzip.seek(65536 - 8)
        assert 65536 - 8 == blockgzip.tell()
        assert content[65536 - 8 : 65536 + 8] == blockgzip.read(16)
        assert 65536 + 8 == blockgzip.tell()

        #    def test_block_span(self, test_txt, test_blockgz):
        #        content = test_txt.read()
        #        blockgzip = BGZipSeek(test_blockgz)
        blockgzip.seek(0)
        assert 0 == blockgzip.tell()
        assert content[: 65536 + 8] == blockgzip.read(65536 + 8)
        assert 65536 + 8 == blockgzip.tell()
