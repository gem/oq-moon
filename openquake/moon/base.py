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
from utils import TimeoutError, NotUniqError, wait_for
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class Moon(object):
    DT = 0.1

    def __init__(self, user=None, passwd=None, email=None):

        self.driver = None
        self.basepath = None
        self.user = user
        self.passwd = passwd
        self.email = email
        self.debugger = None
        self.users = []
        self.platforms = []  # secondary platforms only
        self.is_logged = False

    def init(self, config=None):
        if not config:
            # we import configuration variables here to keep highest
            # level of isolation without creating unnecessary globals
            try:
                from moon_config import (
                    pla_basepath, pla_user, pla_passwd, pla_email, pla_debugger)
            except ImportError as exc:
                sys.stderr.write(exc + "\n")
                sys.exit("ERROR: config.py not found or incomplete. "
                         "Copy config.py.tmpl in config.py and modify "
                         "it properly or check if config.py.tmpl has "
                         "any new fields.")
        else:
            pla_basepath, pla_user, pla_passwd, pla_email, pla_debugger = config

        self.debugger = pla_debugger
        self.driver = self.driver_create("firefox", self.debugger)
        self.basepath = pla_basepath
        if not self.user:
            self.user = pla_user
        if not self.passwd:
            self.passwd = pla_passwd
        if not self.email:
            self.email = pla_email

        self.driver.maximize_window()
        self.main_window = None
        time.sleep(5)
        if self.homepage_login():
            self.is_logged = True
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
                fp.set_preference("extensions.firebug.allPagesActivation",
                                  "on")
                fp.set_preference("extensions.firebug.console.enableSites",
                                  True)
                fp.set_preference("extensions.firebug.defaultPanelName",
                                  "console")
            if sel_vers_maj > 2:
                firefox_capabilities = webdriver.common.desired_capabilities.DesiredCapabilities.FIREFOX
                firefox_capabilities['marionette'] = True
                driver = webdriver.Firefox(firefox_profile=fp, capabilities=firefox_capabilities)
            else:
                driver = webdriver.Firefox(firefox_profile=fp)
        else:
            driver = None

        return driver

    def platform_create(self, user, passwd):
        pl = self.__class__(user, passwd)
        self.platforms.append(pl)
        return pl

    def platform_destroy(self, pl):
        self.platforms.remove(pl)
        pl.fini()

    def homepage_login(self):
        self.driver.get(self.basepath)
        if not self.main_window:
            self.main_window = self.current_window_handle()
            try:
                self.driver.switch_to_window(self.main_window)
            except WebDriverException:
                self.main_window = None

        # <a class="dropdown-toggle" data-toggle="dropdown" href="#">
        #Sign in</a>
        inputs = self.driver.find_elements(By.XPATH, "//a[text()='Sign in']")
        if len(inputs) != 1:
            return False
        inputs[0].click()

        #<input id="id_username" type="text" name="username">
        #<label for="id_password">Password:</label>
        #<input id="id_password" type="password" name="password">
        #<label class="checkbox">
        user_field = self.xpath_finduniq(
            "//input[@id='id_username' and @type='text' "
            "and @name='username']")
        user_field.send_keys(self.user)

        passwd_field = self.xpath_finduniq(
            "//input[@id='id_password' and @type='password' "
            "and @name='password']")
        passwd_field.send_keys(self.passwd)

        #<button class="btn pull-right" type="submit">Sign in</button>
        submit_button = self.xpath_finduniq(
            "//button[@type='submit' and text()='Sign in']")
        submit_button.click()

        inputs = self.driver.find_elements(By.XPATH, "//a[text()='Sign in']")
        if len(inputs) == 1:
            return False
        else:
            return True

    def waituntil(self, delay, action):
        WebDriverWait(self.driver, delay, action)

    def waituntil_js(self, delay, action_js):
        self.waituntil(delay, self.driver.execute_script(action_js))

    @property
    def url(self):
        return self.driver.current_url

    def user_add(self, user, passwd, email):
        self.driver.get(self.basepath + "/admin/auth/user/add/")
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
            "//input[@id='id_email' and @type='text' and @name='email']")
        email_field.send_keys(email)

        # <div class="submit-row">
        # <input class="default" type="submit" name="_save" value="Save">
        submit_button = self.xpath_finduniq(
            "//div[@class='submit-row']"
            "/input[@type='submit' and @name='_save' and @value='Save']")
        submit_button.click()

        self.users.append(user)

    def user_del(self, user):
        self.driver.get(self.basepath + "/admin/auth/user/")

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

    def fini(self):
        self.cleanup()
        # return to main window
        self.windows_reset()

        if not self.is_logged:
            print "WARNING: %s.fini without user (%s)" % (
                self.__class__, self.user)
            self.driver.quit()
            return

        # try to find logout button (in the header)
        try:
            user_button = self.xpath_finduniq(
                "//a[@href='#' and b[@class='caret']]")
        except (TimeoutError, ValueError, NotUniqError):
            self.driver.get(self.basepath)
            time.sleep(3)
            user_button = self.xpath_finduniq(
                "//a[@href='#' and b[@class='caret']]")

        #<a class="dropdown-toggle" data-toggle="dropdown" href="#">
        #nastasi
        #<b class="caret"></b>
        #</a>

        user_button.click()

        #<a href="/account/logout/">
        #<i class="icon-off"></i>
        #Log out
        #</a>
        logout_button = self.xpath_finduniq(
            "//a[@href='/account/logout/' and normalize-space(text())"
            " = 'Log out']")

        logout_button.click()

        #check new url
        self.wait_new_page(logout_button, '/account/logout/')

        #<button class="btn btn-primary" type="submit">Log out</button>
        logout_button = self.xpath_finduniq(
            "//button[@type='submit' and normalize-space("
            "text()) = 'Log out']")
        logout_button.click()

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
        self.wait_new_page(dest_button, '/%s/' % dest)

    def get(self, url):
        self.driver.get(self.basepath + url)

    def xpath_finduniq(self, xpath_str, times=50, postfind=0.1):
        for t in range(0, times):
            field = self.driver.find_elements(By.XPATH, xpath_str)
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

        if len(field) > 1:
            raise NotUniqError(
                "Waiting for '{}' returned {} matches.".format(xpath_str,
                                                               len(field))
                )

        if postfind > 0:
            time.sleep(postfind)
        return field[0]

    def wait_new_page(self, element, url):
        from selenium.common.exceptions import StaleElementReferenceException

        def link_has_gone_stale():
            try:
                # poll the link with an arbitrary call
                element.find_elements_by_id('doesnt-matter')
                return False
            except StaleElementReferenceException:
                if (self.driver.current_url == url
                        or self.driver.current_url == (self.basepath + url)):
                    return True
                else:
                    raise ValueError
        wait_for(link_has_gone_stale)

    def screenshot(self, filename):
        if not self.driver:
            sys.stderr.write(
                "%s not initialized, screenshot impossible.\n" % self.__class__)
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
        for option in sel_obj.find_elements_by_tag_name('option'):
            if option.text == name:
                option.click()  # select() in earlier versions of webdriver
                break

    def select_window_by_name(self, title):
        win_cur = self.current_window_handle()
        for handle in self.driver.window_handles:
            self.switch_to_window(handle)
            if self.driver.title == title:
                return True
        else:
            self.switch_to_window(win_cur)
        raise ValueError

    def select_main_window(self):
        if self.main_window:
            self.switch_to_window(self.main_window)

    def windows_reset(self):
        print self.driver.window_handles
        for handle in self.driver.window_handles:
            if handle == self.main_window:
                continue
            self.switch_to_window(handle)
            self.driver.close()
        self.switch_to_window(self.main_window)

    def window_close(self):
        self.driver.close()

    def current_window_handle(self):
        return self.driver.current_window_handle

    def switch_to_alert(self):
        return self.driver.switch_to_alert()

    def switch_to_window(self, handle):
        return self.driver.switch_to_window(handle)
