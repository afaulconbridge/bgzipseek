"""

Much of this was inspired by https://biopython.org/DIST/docs/api/Bio.bgzf-pysrc.html which is MIT licensed

BGZip format is documented inside https://samtools.github.io/hts-specs/SAMv1.pdf

"""

import io
import struct
import zlib


class BGZipSeek(io.BufferedIOBase):
    def __init__(self, raw):
        self.raw = raw
        self.position = 0
        self.blocksizes_compressed = []
        self.blocksizes_uncompressed = []
        # TODO do on first use, not initialization
        self._preload_blocksizes()
        self.block_uncompressed_index = 0
        self.block_uncoompressed = None
        self._uncompress_block(0)

    def _preload_blocksizes(self):
        offset = 0
        while True:
            compressed_size = self._get_block_size_compressed(offset)
            if not compressed_size:
                # last block in file
                break
            uncompressed_size = self._get_block_size_uncompressed(
                offset, compressed_size
            )
            self.blocksizes_compressed.append(compressed_size)
            self.blocksizes_uncompressed.append(uncompressed_size)
            # move to next block
            offset = offset + compressed_size
        # TODO check valid end of file empty block

    def _get_block_size_compressed(self, block_offset):
        # read the first few bytes of the block from the source
        # TODO validate this is a sensible block
        self.raw.seek(block_offset + 16)
        block_header = self.raw.read(2)
        assert len(block_header) <= 2, len(block_header)
        if len(block_header) == 0:
            # block not in file, end
            return None
        block_size_compressed = struct.unpack("<H", block_header)[0] + 1
        return block_size_compressed

    def _get_block_size_uncompressed(self, block_offset, compressed_size):
        # read the last few bytes of the block from the source
        # TODO validate this is a sensible block
        self.raw.seek(block_offset + compressed_size - 4)
        block_footer = self.raw.read(4)
        if len(block_footer) == 0:
            # block not in file, end
            return 0
        block_size_uncompressed = struct.unpack("<I", block_footer)[0]

        assert block_size_uncompressed <= 65536, block_size_uncompressed

        return block_size_uncompressed

    def _uncompress_block(self, i):
        compressed_offset = sum(self.blocksizes_compressed[:i])
        self.raw.seek(compressed_offset)
        compressed_bytes = self.raw.read(self.blocksizes_compressed[i])
        assert len(compressed_bytes) == self.blocksizes_compressed[i]

        decompressor = zlib.decompressobj(15 + 32)
        uncompressed_bytes = decompressor.decompress(compressed_bytes)

        assert self.blocksizes_uncompressed[i] == len(uncompressed_bytes), i

        assert not decompressor.unconsumed_tail, len(decompressor.unconsumed_tail)
        assert not decompressor.unused_data, len(decompressor.unused_data)

        self.block_uncompressed_index = i
        self.block_uncoompressed = uncompressed_bytes

    def _find_block_index(self, uncompressed_offset):
        i = 0
        uncompressed_running_total = 0
        while i < len(self.blocksizes_uncompressed):
            uncompressed_running_total += self.blocksizes_uncompressed[i]
            if uncompressed_running_total > uncompressed_offset:
                return i

            i += 1
        return None  # not inside any blocks

    def __repr__(self):
        return f"BlockGZip({self.raw})"

    @property
    def size(self):
        # TODO calculate once and store
        return sum(self.blocksizes_uncompressed)

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            if offset < 0:
                raise OSError("Unable to seek before start")
            # seeking past the end is permitted
            self.position = offset
        elif whence == io.SEEK_CUR:
            if self.position + offset < 0:
                raise OSError("Unable to seek before start")
            # seeking past the end is permitted
            self.position += offset
        elif whence == io.SEEK_END:
            if offset < -self.size:
                raise OSError("Unable to seek before start")
            self.position = self.size + offset
        else:
            raise ValueError(
                "invalid whence (%r, should be %d, %d, %d)"
                % (whence, io.SEEK_SET, io.SEEK_CUR, io.SEEK_END)
            )

        block_index_updated = self._find_block_index(self.position)
        if (
            block_index_updated is not None
            and block_index_updated != self.block_uncompressed_index
        ):
            self._uncompress_block(block_index_updated)

        return self.position

    def readable(self):
        return True

    def read(self, size=-1):
        if size >= 0:
            return self.read1(size)
        else:
            return self.read1(self.size - self.position)

    def read1(self, size):
        value = b""
        block_position = self.position - sum(
            self.blocksizes_uncompressed[: self.block_uncompressed_index]
        )
        value_extra = self.block_uncoompressed[block_position : block_position + size]
        if not value_extra:
            return value
        assert len(value_extra)
        assert len(value_extra) <= size
        value = value + value_extra
        size -= len(value_extra)
        self.seek(len(value_extra), io.SEEK_CUR)
        if size:
            # move forward, loading next block if necessary
            value = value + self.read1(size)
        return value

    def writable(self):
        return False

    def truncate(self):
        raise OSError("not writable")

    def write(self, bytes_to_write):
        raise OSError("not writable")
