#!/usr/bin/env python
import unittest
import time
from openquake.moon.test import pla
from selenium.webdriver.common.keys import Keys

class ScrollTest(unittest.TestCase):
    def scroll_to_a_test(self):
        pla.get('/scroll_test.html')

        hyperlink_res = pla.xpath_finduniq("//div[@id='hyperlink-click']",
                                           100, 1)
        hyperlink = pla.xpath_finduniq("//a[normalize-space(text())='hyperlink']",
                                       100, 1)
        hyperlink.click()

        hyperlink_res = pla.xpath_finduniq("//div[@id='hyperlink-click']",
                                           100, 1)
        self.assertFalse(not hyperlink_res.is_displayed())
        
        internal = pla.xpath_finduniq(
            "//a[normalize-space(text())='internal']",
            100, 1)
        internal.click()
        internal_res = pla.xpath_finduniq(
            "//div[@id='internal-click']", 100, 1)
        self.assertFalse(not internal_res.is_displayed())

