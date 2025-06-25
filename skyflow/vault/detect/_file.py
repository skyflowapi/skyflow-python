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

    def get_file(self) -> dict:
        """Get file and its metadata"""
        if not self.file:
            return None
        return {
            "file": self.file,
            "name": self.name,
            "size": self.size,
            "type": self.type,
            "last_modified": self.last_modified
        }

    # Add file-like interface methods that delegate to the underlying BytesIO
    def seek(self, offset, whence=0):
        """Delegate seek operation to underlying BytesIO"""
        if self.file:
            return self.file.seek(offset, whence)
        raise AttributeError("No file available")

    def read(self, size=-1):
        """Delegate read operation to underlying BytesIO"""
        if self.file:
            return self.file.read(size)
        raise AttributeError("No file available")

    def tell(self):
        """Delegate tell operation to underlying BytesIO"""
        if self.file:
            return self.file.tell()
        raise AttributeError("No file available")

    def write(self, data):
        """Delegate write operation to underlying BytesIO"""
        if self.file:
            return self.file.write(data)
        raise AttributeError("No file available")
