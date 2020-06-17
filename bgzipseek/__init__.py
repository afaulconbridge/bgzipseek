import io
import struct
import zlib

"""

Much of this was inspired by https://biopython.org/DIST/docs/api/Bio.bgzf-pysrc.html which is MIT licensed

BGZip format is documented inside https://samtools.github.io/hts-specs/SAMv1.pdf

"""

bgzf_header = b"\x1f\x8b\x08\x04\x00\x00\x00\x00\x00\xff\x06\x00\x42\x43\x02\x00"


class BGZipSeekReader(io.RawIOBase):
    def __init__(self, fileobj):
        self.fileobj = fileobj
        self.is_closed = False
        self.file_offset = 0
        self.blocksizes_compressed = []
        self._preload_blocksizes_compressed()  # TODO do on first use, not initialization
        self.blocksize = self.blocksizes_compressed[
            0
        ]  # assume all blocks sized as first

    def read(self, size):
        if size < 0:
            raise NotImplementedError

        # get current block start, block end
        initial_offset = self.tell()
        block_i = initial_offset // self.blocksize
        # if its past end of file
        if block_i >= len(self.blocksizes_compressed):
            return b""

        # assume all previous blocks same size uncompressed
        block_offset_uncompressed = block_i * self.blocksize
        block_offset_uncompressed_internal = initial_offset - block_offset_uncompressed

        # TODO make one system call to read `size` compressed bytes, which will include `size` uncompressed bytes

        response = b""
        while len(response) < size:
            block_offset_compressed = (
                sum((x for x in self.blocksizes_compressed[:block_i])) + block_i
            )
            block_size_compressed = self.blocksizes_compressed[block_i]
            block_bytes = self._get_block_content(
                block_offset_compressed, block_size_compressed
            )
            # jump to internal offset
            block_bytes = block_bytes[block_offset_uncompressed_internal:]
            block_offset_uncompressed_internal = 0
            response += block_bytes
            block_i += 1
            # if this was the last block, stop
            if block_i >= len(self.blocksizes_compressed):
                break

        # trim back to fit
        response = response[:size]
        self.file_offset += len(response)
        return response

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            self.file_offset = offset
        elif whence == io.SEEK_CUR:
            self.file_offset += offset
        elif whence == io.SEEK_END:
            # TODO implement this
            raise NotImplementedError
        else:
            raise NotImplementedError
        return self.file_offset

    def _preload_blocksizes_compressed(self):
        offset = 0
        while True:
            size = self._get_block_size_compressed(offset)
            if not size:
                # last block in file
                break
            self.blocksizes_compressed.append(size)
            # move to next block
            offset = offset + size + 1

    def _get_block_size_compressed(self, block_offset):
        # read the first few bytes of the block from the source
        self.fileobj.seek(block_offset + 16)
        block_header = self.fileobj.read(2)
        if len(block_header) == 0:
            # block not in file, end
            return None
        block_size = struct.unpack("<H", block_header)[0]
        return block_size

    # TODO add caching
    def _get_block_content(self, block_offset, block_size):
        self.fileobj.seek(block_offset)
        compressed_bytes = self.fileobj.read(block_size + 1)
        decompressed_bytes = self._decompress_bytes(compressed_bytes)
        return decompressed_bytes

    def _decompress_bytes(self, compressed_bytes):
        decompressor = zlib.decompressobj(15 + 32)
        decompressed_bytes = decompressor.decompress(compressed_bytes)
        assert not decompressor.unconsumed_tail
        assert not decompressor.unused_data
        return decompressed_bytes

    def close(self):
        self.fileobj.close()
        self.is_closed = True

    @property
    def closed(self):
        return self.fileobj.closed

    def tell(self):
        return self.file_offset

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class BGZipSeekWriter(io.RawIOBase):
    def __init__(self, fileobj, blocksize=65536, compresslevel=-1):
        self.fileobj = fileobj
        self.buffered_bytes = b""
        self.blocksize = blocksize
        self.compresslevel = compresslevel

    def close(self):
        self._write_block(self.buffered_bytes)
        self.fileobj.close()

    @property
    def closed(self):
        return self.fileobj.closed

    def readable(self):
        return False

    def writable(self):
        return True

    def write(self, bytes_to_write):
        if self.closed:
            raise ValueError()

        self.buffered_bytes = self.buffered_bytes + bytes_to_write
        written_size = 0
        while len(self.buffered_bytes) > self.blocksize:
            written_size += self._write_block(self.buffered_bytes[: self.blocksize])
            self.buffered_bytes = self.buffered_bytes[self.blocksize :]
        return len(bytes_to_write)

    def _write_block(self, block):
        data = self._compress_block(block)
        self.fileobj.write(data)
        return len(block)

    def _compress_block(self, block):
        """Write to file a single BGZF compressed block."""
        assert len(block) <= self.blocksize, "block too large"

        # -15 is 2**15 window size no header
        c = zlib.compressobj(self.compresslevel, wbits=-15)
        compressed = c.compress(block) + c.flush()
        del c
        assert len(compressed) < self.blocksize, "did not compress"
        crc = zlib.crc32(block)
        # Should cope with a mix of Python platforms...
        if crc < 0:
            crc = struct.pack("<i", crc)
        else:
            crc = struct.pack("<I", crc)
        bsize = struct.pack("<H", len(compressed) + 25)  # includes -1
        crc = struct.pack("<I", zlib.crc32(block) & 0xFFFFFFFF)
        uncompressed_length = struct.pack("<I", len(block))
        # Fixed 16 bytes,
        # gzip magic bytes (4) mod time (4),
        # gzip flag (1), os (1), extra length which is six (2),
        # sub field which is BC (2), sub field length of two (2),
        # Variable data,
        # 2 bytes: block length as BC sub field (2)
        # X bytes: the data
        # 8 bytes: crc (4), uncompressed data length (4)
        data = bgzf_header + bsize + compressed + crc + uncompressed_length

        return data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
