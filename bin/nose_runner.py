#!/usr/bin/env python
import nose

from openquake.moon.failurecatcher import FailureCatcher

if __name__ == '__main__':
    nose.main(addplugins=[FailureCatcher()])
