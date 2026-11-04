"""Package metadata rules: never change root or unrelated host paths on extraction."""
from pathlib import PurePosixPath

PLUGIN = 'parity.check.tuning.plus'


def validate_members(members):
    roots = (f'usr/local/emhttp/plugins/{PLUGIN}', 'usr/local/emhttp/languages')
    ancestors = {'usr','usr/local','usr/local/emhttp','usr/local/emhttp/plugins'}
    for member in members:
        path = PurePosixPath(member.name)
        if member.name in ('.','./','/') or path.is_absolute() or '..' in path.parts:
            raise ValueError(f'Unsafe archive path: {member.name}')
        if member.name not in ancestors and not any(member.name == root or member.name.startswith(root+'/') for root in roots):
            raise ValueError(f'Archive changes an unrelated host path: {member.name}')
        if not (member.isfile() or member.isdir()):
            raise ValueError(f'Unsupported archive entry type: {member.name}')
        if member.uid != 0 or member.gid != 0:
            raise ValueError(f'Archive entry is not root-owned: {member.name}')
        if member.mode & 0o7022:
            raise ValueError(f'Unsafe archive permissions: {member.name}')
        if member.isdir() and member.mode != 0o755:
            raise ValueError(f'Incorrect directory permissions: {member.name}')
