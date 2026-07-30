#!/usr/bin/env python
import unittest
import pytest
# from nose.plugins.attrib import attr
from openquake.moon.test import pla

@pytest.mark.skip(reason="disable screenshots during first phase of nose-pytest migration")
class ScreenshotTest(unittest.TestCase):
#    @attr('negate')
    def screenshot_test(self):
        pla.get('/screenshot_test.html')

        pla.xpath_finduniq("//impossible", 1, 1)
