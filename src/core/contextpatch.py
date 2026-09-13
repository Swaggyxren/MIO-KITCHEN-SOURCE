#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
# Copyright (C) 2022-2025 The MIO-KITCHEN-SOURCE Project
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html#license-text
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Patch file_contexts to add missing SELinux file contexts.
Includes filesystem-aware context sanitization and optimizations
inspired by RomTools by Danda420 (Danda420 <dandagaharu77@gmail.com>).
"""
import os
from re import escape, search
from typing import Any, Generator, Union, Optional
from src.core.utils import JsonEdit


def scan_context(file) -> dict:
    context = {}
    with open(file, "r", encoding='utf-8') as file_:
        for i in file_.readlines():
            if not i.strip():
                print('[W] data is empty!')
                continue
            try:
                filepath, rule, *other = i.strip().split()
            except ValueError:
                continue
            filepath = filepath.replace(r'\@', '@')
            context[filepath] = rule
            if len(other) > 0:
                print(f"[Warn] {i[0]} has too much data.Skip.")
                del context[filepath]
    return context


def scan_dir(folder, fstype: str = 'ext4') -> Generator[Union[str, Any], Optional[Any], None]:  # 读取解包的目录，返回一个字典
    part_name = os.path.basename(folder)
    # EROFS does not support PCRE regex wildcards (/.*)? in file_contexts
    if fstype == 'erofs':
        allfiles = ['/', '/lost+found', f'/{part_name}/lost+found', f'/{part_name}', f'/{part_name}/']
    elif fstype == 'f2fs':
        allfiles = ['/', '/lost+found', f'/{part_name}', f'/{part_name}/', fr'/{part_name}(/.*)?']
    else:
        allfiles = ['/', '/lost+found', f'/{part_name}/lost+found', f'/{part_name}', f'/{part_name}/',
                    fr'/{part_name}(/.*)?']

    for root, dirs, files in os.walk(folder, topdown=True):
        for dir_ in dirs:
            yield os.path.join(root, dir_).replace(folder, '/' + part_name).replace('\\', '/')
        for file in files:
            yield os.path.join(root, file).replace(folder, '/' + part_name).replace('\\', '/')
    yield from allfiles


def str_to_selinux(string: str, fstype: str = 'ext4') -> str:
    if string.endswith('(/.*)?'):
        return string
    return escape(string).replace('\\-', '-')


def match_selinux_rule(pattern: str, path: str) -> bool:
    clean_pattern = pattern
    if not clean_pattern.startswith('^'):
        clean_pattern = '^' + clean_pattern
    if not clean_pattern.endswith('$'):
        clean_pattern = clean_pattern + '$'
    try:
        return bool(search(clean_pattern, path))
    except Exception:
        return False


def context_patch(fs_file: dict, dir_path: str, fix_permission: dict, fstype: str = 'ext4') -> tuple:  # 接收两个字典对比
    new_fs = {}
    r_new_fs = {}
    add_new = 0
    part_name = os.path.basename(os.path.abspath(dir_path)).lower()
    if 'vendor' in part_name or 'odm' in part_name:
        permission_d = 'u:object_r:vendor_file:s0'
    else:
        permission_d = 'u:object_r:system_file:s0'

    # RomTools: For EROFS, purge all regex catch-all rules (/.*)? which break mkfs.erofs
    if fstype == 'erofs':
        filtered_fs = {}
        for k, v in fs_file.items():
            if not k.endswith('(/.*)?') and r'(/.*)?' not in k:
                filtered_fs[k] = v
        fs_file = filtered_fs

    for i in scan_dir(os.path.abspath(dir_path), fstype=fstype):
        if not i.isprintable():
            i = ''.join([c if c.isprintable() or not c.strip(' ') else '*' for c in i])
        i = str_to_selinux(i, fstype=fstype)

        if fs_file.get(i):
            # 如果存在直接使用默认的
            new_fs[i] = fs_file[i]
        else:
            permission = None
            if r_new_fs.get(i):
                continue
            if i:
                # 1. Exact match in fix_permission
                if i in fix_permission:
                    permission = fix_permission[i]
                else:
                    # 2. Specific regex match (longest pattern first so specific rules beat broad catch-alls)
                    for f, perm in sorted(fix_permission.items(), key=lambda x: len(x[0]), reverse=True):
                        if f in ('/', '/lost\\+found', '/lost+found') and i != f:
                            continue
                        if match_selinux_rule(f, i):
                            permission = perm
                            break

                # 3. Safeguard against rootfs:s0 misclassification:
                # Rootfs is strictly for root ramdisk. Files inside partitions must never receive rootfs:s0.
                # Even in system partition, only '/' or root ramdisk entries may be rootfs:s0.
                if permission == 'u:object_r:rootfs:s0':
                    if part_name != 'system' or (i != '/' and not i.startswith('/init') and not i.startswith('/default.prop')):
                        permission = None

                if not permission:
                    # RomTools logic: /bin/ and .sh executables in vendor/odm require vendor_qti_init_shell_exec
                    if ('vendor' in part_name or 'odm' in part_name) and ('/bin/' in i or i.endswith('/bin') or i.endswith('.sh')):
                        permission = 'u:object_r:vendor_qti_init_shell_exec:s0'
                    else:
                        permission = permission_d
            if permission and " " in permission:
                permission = permission.replace(' ', '*')
            print(f"ADD [{i} {permission}]")
            add_new += 1
            r_new_fs[i] = permission
            new_fs[i] = permission

    # RomTools root contexts guarantees:
    # EROFS requires exact root entries: / $context, /$partition $context, /$partition/ $context
    root_context = new_fs.get(f'/{part_name}', permission_d)
    if fstype == 'erofs':
        for root_path in ['/', f'/{part_name}', f'/{part_name}/']:
            if root_path not in new_fs:
                new_fs[root_path] = root_context
                add_new += 1
    elif fstype == 'f2fs':
        if '/' not in new_fs:
            new_fs['/'] = root_context
            add_new += 1
        f2fs_wildcard = f'/{part_name}(/.*)?'
        if f2fs_wildcard not in new_fs:
            new_fs[f2fs_wildcard] = root_context
            add_new += 1

    return new_fs, add_new


def main(dir_path, fs_config, fix_permission_file=None, fstype: str = 'ext4') -> None:
    if fix_permission_file is not None and os.path.exists(fix_permission_file):
        raw_permission: dict = JsonEdit(fix_permission_file).read()
        # Sanitize fix_permission:
        # 1. Root / and lost+found are partition-specific; ignore from global rules
        # 2. Filter out corrupted rootfs:s0 entries for subfiles/partitions
        fix_permission = {}
        for k, v in raw_permission.items():
            if k in ('/', '/lost\\+found', '/lost+found'):
                continue
            if v == 'u:object_r:rootfs:s0' and not (k.startswith('/init') or k == '/default.prop'):
                continue
            fix_permission[k] = v
    else:
        fix_permission = {}
    new_fs, add_new = context_patch(scan_context(os.path.abspath(fs_config)), dir_path, fix_permission, fstype=fstype)
    with open(fs_config, "w+", encoding='utf-8', newline='\n') as f:
        f.writelines([f"{i} {new_fs[i]}\n" for i in sorted(new_fs.keys())])
    print(f'ContextPatcher: Add {add_new:d} entries ({fstype})')

