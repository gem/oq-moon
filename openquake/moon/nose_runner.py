# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016 GEM Foundation
#
# OpenQuake Moon (oq-moon) is free software: you can redistribute it
# and/or modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenQuake Moon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import nose
import sys
import os

from openquake.moon import FailureCatcher

if __name__ == '__main__':
    paths = []
    if 'GEM_OPT_PACKAGES' in os.environ:
        pkgs = os.environ['GEM_OPT_PACKAGES'].split(',')
        for pkg_name in pkgs:
            try:
                pkg = __import__(pkg_name)
                new_path = os.path.join(os.path.dirname(pkg.__file__),
                                        'test')
                if not os.path.isdir(new_path):
                    continue
                print("ADDING NEW TESTS PATH: [%s]" % new_path)
                paths.append(new_path)
            except ImportError:
                pass
        print("TESTS PATHS: %s" % paths)

    nose.main(addplugins=[FailureCatcher()], argv=(sys.argv + paths))
