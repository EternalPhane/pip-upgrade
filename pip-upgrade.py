# encoding: utf-8
# -*- coding: utf-8 -*-

"""Upgrade all out-dated packages using pip."""

import os
import platform
import tempfile
import urllib
import xmlrpc.client

from packaging import version as V
import pip

__author__ = 'EternalPhane'
__copyright__ = 'Copyright (c) 2016 EternalPhane'
__license__ = 'MIT'
__version__ = '0.0.1'
__maintainer__ = 'EternalPhane'
__email__ = 'eternalphane@gmail.com'
__status__ = 'Prototype'


def main():
    def schedule(a, b, c):
        per = 100 * a * b / c
        bar = int(per * 0.2 + 0.5)
        print('\r[%s%s] %.2f%%' % ('=' * bar, ' ' * (20 - bar), 100 if per > 100 else per), end='')

    system = {
        'Windows': 'win',
        'Linux': 'manylinux1',
        'Darwin': 'macos',
        '': ''
    }[platform.system()]
    arch = {
        '32bit': '32' if system == 'win' else 'i686' if system == 'manylinux1' else '',
        '64bit': 'amd64' if system == 'win' else 'x86_64' if system else '',
        '': ''
    }[platform.architecture()[0]]
    impl = platform.python_implementation()
    py_ver = 'cp' + ''.join(platform.python_version_tuple()[:2]) if impl == 'CPython' else 'source'
    pkgs = []
    pypi = xmlrpc.client.ServerProxy('https://pypi.python.org/pypi')
    dists = pip.get_installed_distributions()
    max_len = len(dists[0].project_name)
    for dist in dists:
        dst_len = len(dist.project_name)
        print('Checking %s...%s\r' % (dist.project_name, ' ' * (max_len - dst_len)), end='')
        max_len = dst_len if dst_len > max_len else max_len
        found = False
        for version in sorted(
            (version for version in try_until_success(
                lambda: pypi.package_releases(dist.project_name, True),
                lambda: print('\n')
            ) if V.parse(version) > V.parse(dist.version)),
            key=lambda version: V.parse(version),
            reverse=True
        ):
            for release in try_until_success(
                lambda: pypi.release_urls(dist.project_name, version),
                lambda: print('\n')
            ):
                if (
                    release['python_version'] == py_ver and
                    system in release['filename'] and
                    arch in release['filename']
                ):
                    pkgs.append(type('', (object,), {
                        'name': dist.project_name,
                        'version': (dist.version, version),
                        'filename': release['filename'],
                        'url': release['url']
                    }))
                    found = True
                    break
            if found:
                break
    print('%s\r' % (' ' * (max_len + 12)), end='')
    if len(pkgs):
        print('The following packages will be upgraded:')
        for pkg in pkgs:
            print(' %s (Current: %s Lastest: %s)' % (pkg.name, pkg.version[0], pkg.version[1]))
        if input('Do you want to continue? [Y/n] ') not in 'yY':
            print('Abort.')
        else:
            if tempfile.tempdir is None:
                tempfile.gettempdir()
            for pkg in pkgs:
                print('Downloading %s...' % (pkg.name))
                pkg_cache = try_until_success(
                    lambda: urllib.request.urlretrieve(
                        pkg.url,
                        filename=os.path.join(tempfile.tempdir, pkg.filename),
                        reporthook=schedule
                    ),
                    lambda: None if input('\nDo you want to retry? [Y/n] ') in 'yY' else 0
                )[0]
                print('\nDone.')
                try_until_success(
                    lambda: None if pip.main(['install', pkg_cache]) else 0,
                    lambda: None if input('Do you want to retry? [Y/n] ') in 'yY' else 0
                )
    else:
        print('All packages are already the newest version.')


def try_until_success(try_func, except_func=lambda: None):
    result = None
    err = None
    while result is None and err is None:
        try:
            result = try_func()
        except Exception as e:
            err = except_func()
            print(e)
    return result


if __name__ == '__main__':
    main()