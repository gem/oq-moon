#!/usr/bin/env python
import unittest
from nose.plugins.attrib import attr
from openquake.moon.test import pla

class ScreenshotTest(unittest.TestCase):
    @attr('negate')
    def screenshot_test(self):
        pla.get('/screenshot_test.html')

        pla.xpath_finduniq("//impossible']", 1, 1)
