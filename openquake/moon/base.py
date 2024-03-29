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

import time
import sys
import os
import re
import shutil
from .utils import TimeoutError, NotUniqError, wait_for
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions


class Moon(object):
    DT = 0.1
    # standard waiting time before rise exception (in sec)
    TIMEOUT = 5
    DOWNLOAD_DIRNAME = 'gem-oq-moon-download'
    __primary = None

    def __init__(self, user=None, passwd=None, email=None, jqheavy=False):

        self.driver = None
        self.basepath = None
        self.user = user
        self.passwd = passwd
        self.email = email
        self.debugger = None
        self.users = []
        self.platforms = []  # secondary platforms only
        self.is_logged = False
        self.jqheavy = jqheavy
        self.stats_on = 'OQ_MOON_STATS' in os.environ
        self.header_height = -1
        # not factorized in 'driver_create'
        # if here changes it must be changed accordingly
        self._download_dir = os.path.join(
            os.path.expanduser("~"), Moon.DOWNLOAD_DIRNAME)
        if os.path.isdir(self._download_dir):
            shutil.rmtree(self._download_dir)
        os.mkdir(self._download_dir)

    @property
    def download_dir(self):
        return self._download_dir

    def primary_set(self):
        self.__class__.__primary = self

    def jqheavy_set(self, value):
        self.jqheavy = value

    @classmethod
    def primary_get(cls):
        return(cls.__primary)

    def init(self, landing="", config=None, autologin=True, timeout=3.0):
        if not config:
            # we import configuration variables here to keep highest
            # level of isolation without creating unnecessary globals
            try:
                from moon_config import (
                    pla_basepath, pla_user, pla_passwd,
                    pla_email, pla_debugger)
            except ImportError as exc:
                sys.stderr.write(str(exc) + "\n")
                sys.exit("ERROR: moon_config.py not found or incomplete. "
                         "Copy config.py.tmpl in config.py and modify "
                         "it properly or check if config.py.tmpl has "
                         "any new fields.")
        else:
            (pla_basepath, pla_user, pla_passwd, pla_email, pla_debugger) = config

        self.debugger = pla_debugger
        self.driver = self.driver_create("firefox", self.debugger)
        self.basepath = pla_basepath
        if not self.user:
            self.user = pla_user
        if not self.passwd:
            self.passwd = pla_passwd
        if not self.email:
            self.email = pla_email

        # screencast: comment maximize_window() line
        # if you want to set a specific window size

        # self.driver.maximize_window()
        self.driver.set_window_size("1024", "768")
        self.main_window = None

        self.homepage_login(landing=landing, autologin=autologin,
                            timeout=timeout)
        time.sleep(1)

    @staticmethod
    def driver_create(name, debugger):
        import selenium
        from selenium import webdriver
        sel_vers_maj = int(selenium.__version__.split('.')[0])
        if name == "firefox":
            fp = webdriver.FirefoxProfile()
            if debugger != "":
                fp.add_extension(extension=debugger)
                fp.native_events_enabled = False
                fp.set_preference("browser.tabs.warnOnClose", False)
                fp.set_preference(
                    "extensions.firebug.allPagesActivation", "on")
                fp.set_preference(
                    "extensions.firebug.console.enableSites", True)
                fp.set_preference(
                    "extensions.firebug.defaultPanelName", "console")

            fp.set_preference('browser.download.folderList', 2)
            fp.set_preference(
                'browser.download.manager.showWhenStarting', False)
            fp.set_preference("browser.download.dir", os.path.join(
                os.path.expanduser("~"), Moon.DOWNLOAD_DIRNAME))
            fp.set_preference(
                'browser.helperApps.neverAsk.saveToDisk',
                'text/csv,text/xml,application/zip,image/png')

            if sel_vers_maj > 2 and sel_vers_maj < 4:
                caps = webdriver.common.desired_capabilities
                firefox_capabilities = caps.DesiredCapabilities.FIREFOX
                firefox_capabilities['marionette'] = True

                # screencast: the extension "Hide Tab Bar With One Tab"
                # enable tab hiding if just one tab is opened
                driver = webdriver.Firefox(firefox_profile=fp,
                                           capabilities=firefox_capabilities)

                # screencast: set window position and size when required
                # driver.set_window_position(0, 0)
                # driver.set_window_size(1024, 742)

            if sel_vers_maj >= 4:
                options = FirefoxOptions()
                options.set_preference("browser.download.folderList", 2)
                options.set_preference(
                   'browser.download.manager.showWhenStarting', False)
                options.set_preference("browser.download.dir", os.path.join(
                   os.path.expanduser("~"), Moon.DOWNLOAD_DIRNAME))
                options.set_preference(
                   'browser.helperApps.neverAsk.saveToDisk',
                   'text/csv,text/xml,application/zip,image/png')
                driver = webdriver.Firefox(options=options)
        else:
            driver = None

        return driver

    def wait_visibility(self, item, timeout=None):
        if timeout is None:
            timeout = self.TIMEOUT
        start = time.time()

        while item.is_displayed() is False:
            if time.time() - start < timeout:
                time.sleep(self.DT)
            else:
                raise TimeoutError
        return True

    def platform_create(self, user, passwd, jqheavy=None):
        if jqheavy is None:
            jqheavy = self.jqheavy

        pl = self.__class__(user, passwd, jqheavy=jqheavy)
        self.platforms.append(pl)
        return pl

    def platform_destroy(self, pl):
        self.platforms.remove(pl)
        pl.fini()

    def homepage_login(self, landing="", autologin=True, timeout=3.0):
        self.driver.get(self.basepath + landing)
        if not self.main_window:
            self.main_window = self.current_window_handle()
            try:
                self.driver.switch_to.window(self.main_window)
            except WebDriverException:
                self.main_window = None

        if not autologin:
            return True

        # <a class="dropdown-toggle" data-toggle="dropdown" href="#">
        # Sign in</a>
        input = self.xpath_finduniq("//a[normalize-space(text()) = 'Sign in']")
        input.click()

        try:
            user_field = self.xpath_find(
                "//form[@class='%s' or @class='%s']//input[@id="
                "'id_username' and @type='text' and @name='username']" % (
                    ('sign-in', 'form-signin') if landing == "" else (
                        ('form-horizontal', 'form-horizontal'))))
            passwd_field = self.xpath_find(
                "//form[@class='%s' or @class='%s']//input[@id="
                "'id_password' and @type='password' and @name='password']" % (
                    ('sign-in', 'form-signin') if landing == "" else (
                        ('form-horizontal', 'form-horizontal'))))

        except:
            user_field = self.xpath_find(
                "//form[@class='sign-in' or @class='form-signin']//input[@id="
                "'id_username' and @type='text' and @name='username'] | "
                "//div[@id='SigninModal']//form//input[@id="
                "'id_username' and @type='text' and @name='username']"
            )
            passwd_field = self.xpath_find(
                "//form[@class='sign-in' or @class='form-signin']//input[@id="
                "'id_password' and @type='password' and @name='password'] | "
                "//div[@id='SigninModal']//form//input[@id="
                "'id_password' and @type='password' and @name='password']"
            )

        self.wait_visibility(user_field, 2)
        user_field.send_keys(self.user)

        self.wait_visibility(passwd_field, 1)

        passwd_field.send_keys(self.passwd)

        # <button class="btn pull-right" type="submit">Sign in</button>

        try:
            submit_button = self.xpath_finduniq(
                "//button[@type='submit' and text()='%s']" %
                ("Sign in" if landing == "" else "Log in"))
        except:
            submit_button = self.xpath_finduniq(
                "//button[@type='submit' and text()='Sign in'"
                " or text()='Log in']")
        submit_button.click()

        self.wait_new_page(submit_button, self.basepath + landing,
                           timeout=timeout)

        inputs = self.driver.find_elements(By.XPATH, "//a[text()='Sign in']")
        if len(inputs) == 1:
            return False
        else:
            self.is_logged = True
            return True

    def waituntil(self, delay, action):
        WebDriverWait(self.driver, delay).until(action)

    def waituntil_js(self, delay, action_js):
        def action(driver):
            return driver.execute_script(action_js)

        self.waituntil(delay, action)

    @property
    def url(self):
        return self.driver.current_url

    def user_add(self, user, passwd, email):
        self.driver.get(self.basepath + "/admin/people/profile/add/")
        user_field = self.xpath_finduniq(
            "//input[@id='id_username' and @type='text' "
            "and @name='username']")
        user_field.send_keys(user)

        passwd1_field = self.xpath_finduniq(
            "//input[@id='id_password1' and @type='password' "
            "and @name='password1']")
        passwd1_field.send_keys(passwd)

        passwd2_field = self.xpath_finduniq(
            "//input[@id='id_password2' and @type='password' "
            "and @name='password2']")
        passwd2_field.send_keys(passwd)

        # <div class="submit-row">
        # <input class="default" type="submit" name="_save" value="Save">
        submit_button = self.xpath_finduniq(
            "//div[@class='submit-row']"
            "/input[@type='submit' and @name='_save' and @value='Save']")
        submit_button.click()

        # <h1>Change user</h1>
        self.xpath_finduniq("//h1[normalize-space(text()) = 'Change user']")

        # <input id="id_email" class="vTextField" type="text" name="email"
        #     maxlength="75">
        email_field = self.xpath_finduniq(
            "//input[@id='id_email' and @type='email' and @name='email']")
        email_field.send_keys(email)

        # <div class="submit-row">
        # <input class="default" type="submit" name="_save" value="Save">
        submit_button = self.xpath_finduniq(
            "//div[@class='submit-row']"
            "/input[@type='submit' and @name='_save' and @value='Save']")
        submit_button.click()

        self.users.append(user)

    def user_del(self, user):
        self.driver.get(self.basepath + "/admin/people/profile/")

        # <tr>
        #   <td class="action-checkbox">
        #     <input class="action-select" type="checkbox" value="6"
        #         name="_selected_action">
        #   </td>
        #   <th>
        #     <a href="/admin/auth/user/6/">rabado</a>
        #   </th>
        # </tr>
        del_cbox = self.xpath_finduniq(
            "//tr[th/a[text()='%s']]/td[@class='action-checkbox']/"
            "input[@class='action-select' and @type='checkbox']"
            % user)

        del_cbox.click()

        # <select name="action">
        # <option selected="selected" value="">---------</option>
        # <option value="delete_selected">Delete selected users</option>
        # </select>
        action = self.xpath_finduniq("//select[@name='action']")
        self.select_item_set(action, "Delete selected users")

        # <button class="button" value="0" name="index"
        #     title="Run the selected action" type="submit">Go</button>
        butt = self.xpath_finduniq(
            "//button[@name='index' and @type='submit' and text() = 'Go']")

        butt.click()

        # new page and confirm deletion
        # <input type="submit" value="Yes, I'm sure">
        butt = self.xpath_finduniq(
            "//input[@type=\"submit\" and @value=\"Yes, I'm sure\"]")

        butt.click()

        self.users.remove(user)
        self.get('')

    def fini(self):
        self.cleanup()
        # return to main window
        self.windows_reset()

        if not self.is_logged:
            # print("WARNING: %s.fini without user (%s)" % (
            #     self.__class__, self.user))
            if self.driver is not None:
                self.driver.quit()
            return

        # try to find logout button (in the header)
        try:
            user_button = self.xpath_finduniq(
                "//a[@href='#' and normalize-space(@class)="
                "'dropdown-toggle avatar']", timeout=5.0)
        except (TimeoutError, ValueError, NotUniqError):
            # self.driver.get(self.basepath)
            user_button = self.xpath_finduniq(
                "//a[@href='#' and b[@class='caret']]")

        # <a class="dropdown-toggle" data-toggle="dropdown" href="#">
        # nastasi
        # <b class="caret"></b>
        # </a>

        user_button.click()

        # <a href="/account/logout/">
        # <i class="icon-off"></i>
        # Log out
        # </a>
        logout_button = self.xpath_finduniq(
            "//a[@href='/account/logout/' and normalize-space(text())"
            " = 'Log out']")

        logout_button.click()

        # check new url
        self.wait_new_page(logout_button, '/account/logout')

        # <button class="btn btn-primary" type="submit">Log out</button>
        logout_button = self.xpath_finduniq(
            "//button[@type='submit' and normalize-space("
            "text()) = 'Log out']")
        logout_button.click()

        if self.driver:
            self.driver.quit()

    def cleanup(self):
        # removes secondary platforms
        platforms_loop = self.platforms[:]
        for platform in platforms_loop:
            self.platform_destroy(platform)

        users_loop = self.users[:]
        for user in users_loop:
            self.user_del(user)

    def navigate(self, dest):
        # driver, basepath, self.dest):
        if dest not in ["calc", "explore", "share"]:
            raise ValueError

        try:
            dest_button = self.xpath_finduniq("//a[@href='/%s/']" % dest)
        except (TimeoutError, ValueError, NotUniqError):
            self.driver.get(self.basepath)
            dest_button = self.xpath_finduniq("//a[@href='/%s/']" % dest)

        dest_button.click()
        self.wait_new_page(dest_button, '/%s' % dest)

    def get(self, url):
        self.driver.get(self.basepath + url)

    def xpath_find_base(self, xpath_str, el=None):
        base = el if el else self.driver
        return base.find_elements(By.XPATH, xpath_str)

    def xpath_find_any(self, xpath_str, times=None, postfind=0,
                       timeout=None, el=None):
        if timeout is not None:
            times = int(timeout / self.DT)
        elif times is None:
            times = int(self.TIMEOUT / self.DT)

        for t in range(0, times):
            field = self.xpath_find_base(xpath_str, el=el)
            if len(field) > 0:
                break
            if times > 1:
                time.sleep(self.DT)
        else:
            if times > 1:
                raise TimeoutError(
                    "Timeout waiting '{}' for {} seconds.".format(
                        xpath_str, times * self.DT)
                    )
            else:
                raise ValueError(
                    "Search path '{}' not matches.".format(xpath_str)
                    )

        if postfind > 0:
            time.sleep(postfind)

        return field

    def xpath_find(self, xpath_str, times=None, postfind=0,
                   use_first=False, timeout=None, el=None):
        field = self.xpath_find_any(
            xpath_str, times=times, postfind=postfind,
            timeout=timeout, el=el)

        if use_first is False and len(field) > 1:
            raise NotUniqError(
                "Waiting for '{}' returned {} matches.".format(
                    xpath_str, len(field)))

        return field[0]

    def xpath_finduniq(self, xpath_str, times=None, postfind=0,
                       timeout=None, el=None):
        return self.xpath_find(xpath_str, times=times, postfind=postfind,
                               timeout=timeout, use_first=False, el=el)

    def xpath_findfirst(self, xpath_str, times=None, postfind=0,
                        timeout=None):
        return self.xpath_find(xpath_str, times=times, postfind=postfind,
                               timeout=timeout, use_first=True)

    def xpath_finduniq_coords(self, xpath_str, times=None, postfind=0,
                              timeout=None):

        # wait until the dom item appears, than loop for a while to
        # get its coors
        tail_ptr = self.xpath_finduniq(xpath_str, times, postfind,
                                       timeout)
        for i in range(1, 15):
            try:
                x = tail_ptr.location['x']
                y = tail_ptr.location['y']
                return (tail_ptr, x, y)
            except:
                time.sleep(0.2)
                tail_ptr = self.xpath_finduniq(xpath_str, times, postfind,
                                               timeout)
        raise TimeoutError('coords not found')

    def header_height_store(self, match):
        el = self.xpath_finduniq(match)
        self.header_height = el.size['height']

    def scroll_into_view(self, found_element, match=None):
        if match:
            el = self.xpath_finduniq(match)
            scroll_el_height = el.size['height']
        elif self.header_height >= 0:
            scroll_el_height = self.header_height
        else:
            raise ValueError(
                "match not set nether default obscuring element height set")
        found_element.location_once_scrolled_into_view
        loc = found_element.location

        scr_loc = loc['y'] - scroll_el_height

        self.driver.execute_script(
            "window.scrollTo(0, %d);" % int(scr_loc))

    def wait_new_page_previous(self, element, url, timeout=3.0):
        from selenium.common.exceptions import StaleElementReferenceException

        def link_has_gone_stale():
            try:
                # poll the link with an arbitrary call
                element.find_elements(By.ID, 'doesnt-matter')
                return False
            except StaleElementReferenceException:
                deslashed = self.driver.current_url.rstrip('/')
                if (deslashed == url
                        or deslashed == (self.basepath + url)):
                    return True
                else:
                    raise ValueError("expected %s or %s, received %s" % (
                        url, self.basepath + url, deslashed))
        return wait_for(link_has_gone_stale, timeout=timeout)

    def wait_new_page_next(self, match, url, timeout=3.0):
        start = time.time()
        while True:
            try:
                self.xpath_finduniq(match)
                break
            except Exception as e:
                print("except %s" % e)
                if time.time() - start < timeout:
                    time.sleep(self.DT)
                else:
                    raise TimeoutError
        return True

    def wait_new_page(self, element, url, strategy="previous", jqheavy=None,
                      timeout=3.0):
        '''
            'strategy' could be 'previous' or 'next'
            if 'strategy' is 'previous' wait until the 'element' became invalid
            elif 'strategy' is 'next' try to find a match to 'element' string
            to exit with success
        '''
        start = 0
        if self.stats_on:
            start = time.time()

        if strategy == "previous":
            ret = self.wait_new_page_previous(element, url, timeout=timeout)
        elif strategy == "next":
            ret = self.wait_new_page_next(element, url, timeout=timeout)

        if self.stats_on:
            print("STATS: waited %g secs for [%s]"
                  " with strategy %s" % (time.time() - start, url, strategy))

        if ret is not True:
            return ret

        if jqheavy is None:
            jqheavy = self.jqheavy

        if jqheavy is True:
            iters = int(timeout * 10.0) + 1

            for i in range(1, iters):
                value = self.driver.execute_script(
                    "return(typeof(window.jQuery) == 'function');")
                if value is True:
                    break
                time.sleep(self.DT)
            else:
                raise TimeoutError

            self.driver.execute_script(
                "window.jQuery().ready(function()"
                " { window.gem_moon_is_finished = true });")
            for i in range(1, iters):
                value = self.driver.execute_script(
                    "return window.gem_moon_is_finished")
                if value is True:
                    break
                time.sleep(self.DT)
            else:
                raise TimeoutError

    def screenshot(self, filename):
        if not self.driver:
            sys.stderr.write(
                "%s not initialized,"
                " screenshot impossible.\n" % self.__class__)
            return
        self.driver.get_screenshot_as_file(filename)

    def add_click_event(self):
        self.driver.execute_script('''

    window.pla_click_show = function (x,y) {
        var div = document.createElement("div");
        div.style.left = x+"px";
        div.style.top  = y+"px";
        div.style.position = "fixed";
        div.style.width = "50px";
        div.style.height = "50px";
        div.style.background = "red";
        div.style.opacity = "0.5";
        document.body.appendChild(div);
    };

    window.pla_click = function (x,y){
        var ev = document.createEvent("MouseEvent");
        var el = document.elementFromPoint(x,y);
        console.log(x,y);
        ev.initMouseEvent(
            "click",
            true /* bubble */, true /* cancelable */,
            window, null,
            x, y, x, y, /* coordinates */
            false, false, false, false, /* modifier keys */
            0 /*left*/, null
        );
        el.dispatchEvent(ev);

        // pla_click_show(x,y);
    };

    window.pla_click_doc = function (x,y){
        var ev = document.createEvent("MouseEvent");
        ev.initMouseEvent(
            "click",
            true /* bubble */, true /* cancelable */,
            window, null,
            x, y, 0, 0, /* coordinates */
            false, false, false, false, /* modifier keys */
            0 /*left*/, null
        );
        document.getElementsByTagName("html")[0].dispatchEvent(ev);

        pla_click_show(x,y);
    };

    '''
                                   )

    def click_at(self, x, y):
        self.driver.execute_script('pla_click(%d, %d);' % (x, y))

    @staticmethod
    def select_item_set(sel_obj, name):
        for option in sel_obj.find_elements(By.TAG_NAME, 'option'):
            if option.text == name:
                option.click()  # select() in earlier versions of webdriver
                break

    def select_window_by_name(self, title, timeout=3.0, is_regex=False):
        start = time.time()

        while True:
            win_cur = self.current_window_handle()
            for handle in self.driver.window_handles:
                self.switch_to_window(handle)
                if is_regex is True:
                    if re.search(title, self.driver.title):
                        return True
                else:
                    if self.driver.title == title:
                        return True

            if time.time() - start < timeout:
                time.sleep(self.DT)
            else:
                break

        self.switch_to_window(win_cur)
        raise ValueError

    def select_main_window(self):
        if self.main_window:
            self.switch_to_window(self.main_window)

    def windows_reset(self):
        if self.driver is None:
            return

        # print(self.driver.window_handles)
        if self.driver.window_handles is not None:
            for handle in self.driver.window_handles:
                if handle == self.main_window:
                    continue
                self.switch_to_window(handle)
                self.driver.close()
        if self.main_window is not None:
            self.switch_to_window(self.main_window)

    def window_close(self):
        self.driver.close()

    def current_window_handle(self):
        return self.driver.current_window_handle

    def switch_to_alert(self):
        return self.driver.switch_to.alert()

    def switch_to_window(self, handle):
        return self.driver.switch_to.window(handle)
