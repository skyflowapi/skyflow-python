import io
import mimetypes
import time

class File:
    def __init__(self, file: io.BytesIO = None):
        self.file = file
    
    @property
    def name(self) -> str:
        """Get file name"""
        if self.file:
            return getattr(self.file, 'name', 'unknown')
        return None

    @property
    def size(self) -> int:
        """Get file size in bytes"""
        if self.file:
            pos = self.file.tell()
            self.file.seek(0, io.SEEK_END)
            size = self.file.tell()
            self.file.seek(pos)
            return size
        return None

    @property
    def type(self) -> str:
        """Get file mime type"""
        if self.file:
            return mimetypes.guess_type(self.name)[0] or ''
        return None

    @property
    def last_modified(self) -> int:
        """Get file last modified timestamp in milliseconds"""
        if self.file:
            return int(time.time() * 1000)
        return None

    def seek(self, offset, whence=0):
        if self.file:
            return self.file.seek(offset, whence)

    def read(self, size=-1):
        if self.file:
            return self.file.read(size)

    def __repr__(self):
        return (
            f"File(name={self.name!r}, size={self.size!r}, type={self.type!r}, "
            f"last_modified={self.last_modified!r})"
        )    
