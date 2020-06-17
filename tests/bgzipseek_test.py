import io
import itertools
import os
import random
import tempfile

import pytest

from bgzipseek import BGZipSeekReader, BGZipSeekWriter


@pytest.fixture
def temporary_filename():
    temporary_file = tempfile.NamedTemporaryFile(delete=False)
    temporary_filename = temporary_file.name
    temporary_file.close()
    yield temporary_file.name
    os.remove(temporary_filename)


def random_content_generator(rng):
    while True:
        line = " ".join(
            (
                "".join(
                    (rng.choices("abcdefghijklmnopqrstuvwxyz", k=rng.randint(5, 25)))
                )
                for i in range(rng.randint(5, 50))
            )
        )
        yield line


@pytest.fixture
def random_content():
    rng = random.Random(42)
    content = ("\n".join(itertools.islice(random_content_generator(rng), 25))).encode(
        "utf-8"
    )
    return content


@pytest.fixture
def bgzip_filename_to_read(temporary_filename, random_content):
    with BGZipSeekWriter(open(temporary_filename, "wb"), blocksize=1024) as bgzipwriter:
        bgzipwriter.write(random_content)
    yield temporary_filename


class TestBGZipSeekReader:
    def test_basic(self, bgzip_filename_to_read, random_content):
        with BGZipSeekReader(open(bgzip_filename_to_read, "rb")) as bgzipreader:
            read_content = bytes(bgzipreader.read(len(random_content) + 10))
            assert random_content[-20:] == read_content[-20:]
            assert random_content[:20] == read_content[:20]
            assert len(random_content) == len(read_content)

    def test_chunks(self, bgzip_filename_to_read, random_content):
        with BGZipSeekReader(open(bgzip_filename_to_read, "rb")) as bgzipreader:
            read_content = bytes(bgzipreader.read(32))
            assert random_content[:32] == read_content
            assert 32 == bgzipreader.tell()
            read_content = bytes(bgzipreader.read(32))
            assert random_content[32:64] == read_content

    def test_seek(self, bgzip_filename_to_read, random_content):
        with BGZipSeekReader(open(bgzip_filename_to_read, "rb")) as bgzipreader:
            assert bgzipreader.seekable

            assert bgzipreader.seek(32, io.SEEK_SET)
            read_content = bytes(bgzipreader.read(32))
            assert random_content[32:64] == read_content

            assert bgzipreader.seek(32, io.SEEK_CUR)
            read_content = bytes(bgzipreader.read(32))
            assert random_content[96:128] == read_content


class TestBGZipSeekWriter:
    def test_basic(self, temporary_filename, random_content):
        with BGZipSeekWriter(open(temporary_filename, "wb")) as bgzipwriter:
            written_size = bgzipwriter.write(random_content)
            assert written_size == len(random_content)

    def test_closing(self, temporary_filename, random_content):
        with BGZipSeekWriter(open(temporary_filename, "wb")) as bgzipwriter:
            bgzipwriter.write(random_content)
            assert not bgzipwriter.closed

        assert bgzipwriter.closed

        with pytest.raises(ValueError):
            bgzipwriter.write(random_content)

        assert not bgzipwriter.readable()
        with open(temporary_filename, "rb") as rawfile:
            assert 0 < len(rawfile.read())
