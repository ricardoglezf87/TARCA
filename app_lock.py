# -*- coding: utf-8 -*-
import os
import tempfile


class SingleInstanceLock:
    def __init__(self, file_handle):
        self._file_handle = file_handle

    def release(self):
        if not self._file_handle:
            return

        try:
            if os.name == "nt":
                import msvcrt

                self._file_handle.seek(0)
                msvcrt.locking(self._file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._file_handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._file_handle.close()
            self._file_handle = None


def acquire_single_instance_lock():
    lock_path = os.path.join(tempfile.gettempdir(), "tarca_single_instance.lock")
    file_handle = open(lock_path, "a+")

    try:
        if os.name == "nt":
            import msvcrt

            file_handle.seek(0)
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        file_handle.close()
        return None

    file_handle.seek(0)
    file_handle.truncate()
    file_handle.write(str(os.getpid()))
    file_handle.flush()
    return SingleInstanceLock(file_handle)
