"""Fixed Linux root-controller -> model UID launch boundary.

Install this source and its Python runtime in an immutable trusted image. The
controller must scrub environment BEFORE starting Python; this module cannot
protect interpreter startup. No shell, configurable argv or inherited env.
"""
import argparse
import ctypes
import errno
import hashlib
import json
import os
import posixpath
import stat
import sys

MODEL_ID = 65534
POLICY_KEYS = frozenset(('executable', 'executable_sha256', 'model_home',
                         'codex_home', 'config_sha256', 'workspace_root'))


class BoundaryError(Exception):
    """Launch refused before model execution."""


def _canonical(value):
    return (isinstance(value, str) and len(value) > 1 and value.startswith('/')
            and not any(c in value for c in ('\0', '\r', '\n'))
            and posixpath.normpath(value) == value)


def parse_policy(raw):
    """Validate bounded JSON without touching policy-named filesystem paths."""
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise BoundaryError('duplicate policy field')
            result[key] = value
        return result

    try:
        if not isinstance(raw, str) or len(raw.encode('utf-8')) > 65536:
            raise BoundaryError('policy size invalid')
        value = json.loads(raw, object_pairs_hook=pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(
                               BoundaryError('nonfinite policy value')))
        if not isinstance(value, dict) or set(value) != POLICY_KEYS:
            raise BoundaryError('policy fields invalid')
        for key in ('executable', 'model_home', 'codex_home', 'workspace_root'):
            if not _canonical(value[key]):
                raise BoundaryError('policy path invalid')
        for key in ('executable_sha256', 'config_sha256'):
            digest = value[key]
            if (not isinstance(digest, str) or len(digest) != 64
                    or any(c not in '0123456789abcdef' for c in digest)):
                raise BoundaryError('policy digest invalid')
        return value
    except (ValueError, TypeError, UnicodeError) as exc:
        raise BoundaryError('policy JSON invalid') from exc


def _trusted(st):
    return st.st_uid == 0 and not st.st_mode & 0o022


def _open_path(path, *, directory=False, final_model=False):
    """Walk by held no-follow dirfds; never trust a writable ancestor."""
    if not _canonical(path):
        raise BoundaryError('noncanonical path')
    current = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        if not _trusted(os.fstat(current)):
            raise BoundaryError('untrusted root directory')
        parts = path.split('/')[1:]
        for index, part in enumerate(parts):
            final = index == len(parts) - 1
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
            if not final or directory:
                flags |= os.O_DIRECTORY
            next_fd = os.open(part, flags, dir_fd=current)
            os.close(current)
            current = next_fd
            info = os.fstat(current)
            acceptable = _trusted(info)
            if final and final_model:
                acceptable = acceptable or (info.st_uid == MODEL_ID
                                              and not info.st_mode & 0o022)
            if not acceptable:
                raise BoundaryError('untrusted path ownership or permissions')
            if (not final or directory) and not stat.S_ISDIR(info.st_mode):
                raise BoundaryError('directory required')
            if final and not directory and not stat.S_ISREG(info.st_mode):
                raise BoundaryError('regular file required')
        result = current
        current = -1
        return result
    finally:
        if current >= 0:
            os.close(current)


def _read(fd, limit):
    result = bytearray()
    while len(result) <= limit:
        block = os.read(fd, min(65536, limit + 1 - len(result)))
        if not block:
            return bytes(result)
        result.extend(block)
    raise BoundaryError('trusted input too large')


def _digest(fd):
    value = hashlib.sha256()
    while True:
        block = os.read(fd, 1024 * 1024)
        if not block:
            return value.hexdigest()
        value.update(block)


def _check_stdio():
    for fd in (0, 1, 2):
        info = os.fstat(fd)
        if (not stat.S_ISFIFO(info.st_mode) or info.st_uid != 0
                or info.st_mode & 0o077):
            raise BoundaryError('root-created private stdio pipes required')


def _model_directory(path, *, home=False):
    fd = _open_path(path, directory=True, final_model=True)
    try:
        info = os.fstat(fd)
        if home and (info.st_uid != MODEL_ID or stat.S_IMODE(info.st_mode) != 0o700):
            raise BoundaryError('private model home required')
        return fd
    except BaseException:
        os.close(fd)
        raise


def _open_workspace(policy_root, workspace):
    if not _canonical(workspace):
        raise BoundaryError('workspace invalid')
    if workspace != policy_root and not workspace.startswith(policy_root + '/'):
        raise BoundaryError('workspace outside policy root')
    fd = _model_directory(policy_root)
    try:
        suffix = workspace[len(policy_root):].lstrip('/')
        for part in suffix.split('/') if suffix else ():
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                            | os.O_CLOEXEC, dir_fd=fd)
            os.close(fd); fd = child
            info = os.fstat(fd)
            if not (_trusted(info) or (info.st_uid == MODEL_ID and not info.st_mode & 0o022)):
                raise BoundaryError('untrusted workspace directory')
        result = fd; fd = -1
        return result
    finally:
        if fd >= 0:
            os.close(fd)


def _drop_privileges():
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.restype = ctypes.c_int

    def prctl(option, argument=0, extra=0):
        if libc.prctl(option, argument, extra, 0, 0) != 0:
            raise BoundaryError('kernel privilege restriction failed')

    prctl(38, 1)  # PR_SET_NO_NEW_PRIVS, inherited through exec/children.
    prctl(47, 4)  # PR_CAP_AMBIENT / PR_CAP_AMBIENT_CLEAR_ALL.
    # Drop every supported bounding bit, refusing partial enforcement. Needs
    # CAP_SETPCAP in controller; model retains none.
    for capability in range(64):
        ctypes.set_errno(0)
        result = libc.prctl(23, capability, 0, 0, 0)  # PR_CAPBSET_READ
        if result < 0:
            if ctypes.get_errno() == errno.EINVAL:
                break
            raise BoundaryError('cannot inspect capability bounding set')
        if result:
            prctl(24, capability)  # PR_CAPBSET_DROP
    else:
        raise BoundaryError('unsupported capability range')
    prctl(8, 0)  # PR_SET_KEEPCAPS.
    os.setgroups([])
    os.setresgid(MODEL_ID, MODEL_ID, MODEL_ID)
    os.setresuid(MODEL_ID, MODEL_ID, MODEL_ID)

    class Header(ctypes.Structure):
        _fields_ = [('version', ctypes.c_uint32), ('pid', ctypes.c_int)]

    class Data(ctypes.Structure):
        _fields_ = [('effective', ctypes.c_uint32), ('permitted', ctypes.c_uint32),
                    ('inheritable', ctypes.c_uint32)]

    header = Header(0x20080522, 0)
    data = (Data * 2)()
    if libc.capset(ctypes.byref(header), ctypes.byref(data)) != 0:
        raise BoundaryError('cannot clear capability sets')
    if (os.getresuid() != (MODEL_ID,) * 3 or os.getresgid() != (MODEL_ID,) * 3
            or os.getgroups()):
        raise BoundaryError('identity drop incomplete')
    if libc.capget(ctypes.byref(header), ctypes.byref(data)) != 0 or any(
            item.effective or item.permitted or item.inheritable for item in data):
        raise BoundaryError('capability drop incomplete')
    if libc.prctl(39, 0, 0, 0, 0) != 1:  # PR_GET_NO_NEW_PRIVS
        raise BoundaryError('no_new_privs missing')


def launch(policy_path, workspace):
    """Replace this root launcher with the fixed unprivileged native appserver."""
    if sys.platform != 'linux' or os.getresuid() != (0, 0, 0):
        raise BoundaryError('Linux root controller required')
    _check_stdio()
    descriptors = []
    try:
        policy_fd = _open_path(policy_path); descriptors.append(policy_fd)
        if stat.S_IMODE(os.fstat(policy_fd).st_mode) != 0o600:
            raise BoundaryError('private policy required')
        policy = parse_policy(_read(policy_fd, 65536).decode('utf-8'))
        executable_fd = _open_path(policy['executable']); descriptors.append(executable_fd)
        executable_info = os.fstat(executable_fd)
        if executable_info.st_mode & 0o6000 or not executable_info.st_mode & 0o111:
            raise BoundaryError('unsafe executable mode')
        if os.read(executable_fd, 4) != b'\x7fELF':
            raise BoundaryError('native ELF executable required')
        os.lseek(executable_fd, 0, os.SEEK_SET)
        if _digest(executable_fd) != policy['executable_sha256']:
            raise BoundaryError('executable digest changed')
        home_fd = _model_directory(policy['model_home'], home=True); descriptors.append(home_fd)
        codex_fd = _open_path(policy['codex_home'], directory=True); descriptors.append(codex_fd)
        if stat.S_IMODE(os.fstat(codex_fd).st_mode) != 0o755:
            raise BoundaryError('immutable CODEX_HOME required')
        config_fd = _open_path(policy['codex_home'] + '/config.toml'); descriptors.append(config_fd)
        if _digest(config_fd) != policy['config_sha256']:
            raise BoundaryError('config digest changed')
        auth_fd = os.open('auth.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
                          | os.O_NONBLOCK, dir_fd=codex_fd)
        descriptors.append(auth_fd)
        auth_info = os.fstat(auth_fd)
        if (not stat.S_ISREG(auth_info.st_mode) or auth_info.st_uid != MODEL_ID
                or stat.S_IMODE(auth_info.st_mode) != 0o600 or auth_info.st_nlink != 1):
            raise BoundaryError('private model-only auth required')
        workspace_fd = _open_workspace(policy['workspace_root'], workspace)
        descriptors.append(workspace_fd)
        os.fchdir(workspace_fd)
        # /proc is trusted kernel mount in the provisioned host/container TCB.
        # Enumerate actual descriptors, including those above a lowered rlimit.
        for name in os.listdir('/proc/self/fd'):
            fd = int(name)
            if fd > 2 and fd != executable_fd:
                try:
                    os.close(fd)
                except OSError as exc:
                    if exc.errno != errno.EBADF:
                        raise
        descriptors = [executable_fd]
        _drop_privileges()
        environment = dict(HOME=policy['model_home'], CODEX_HOME=policy['codex_home'],
                           PATH='/usr/bin:/bin', LANG='C.UTF-8')
        os.execve(executable_fd, [policy['executable'], 'app-server', '--strict-config'], environment)
    finally:
        for fd in descriptors:
            try:
                os.close(fd)
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(description='Fixed protected model launch')
    parser.add_argument('--policy', required=True)
    parser.add_argument('--workspace', required=True)
    args = parser.parse_args()
    try:
        launch(args.policy, args.workspace)
    except (BoundaryError, OSError, ValueError, UnicodeError):
        # Do not expose policy contents, secret values or hostile path text.
        print('model launch boundary refused', file=sys.stderr)
        return 1
    return 1


if __name__ == '__main__':
    sys.exit(main())
