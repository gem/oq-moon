#!/bin/bash
sudo systemctl stop apt-daily.timer
BRANCH_ID="$1"

#display each command before executing it
set -x
. .gem_init.sh

#apt-get update/upgrade
sudo apt-get -y update
sudo apt-get -y upgrade

#function complete procedure for tests
exec_test () {    
    #install selenium,pip,geckodriver,clone oq-moon and execute tests with nose 
    sudo apt-get -y install python-pip bc
    sudo pip install --upgrade pip
    sudo pip install nose

    wget "http://ftp.openquake.org/common/selenium-deps"
    GEM_FIREFOX_VERSION="$(dpkg-query --show -f '${Version}' firefox)"
    . selenium-deps
    wget "http://ftp.openquake.org/mirror/mozilla/geckodriver-v${GEM_GECKODRIVER_VERSION}-linux64.tar.gz"
    tar zxvf "geckodriver-v${GEM_GECKODRIVER_VERSION}-linux64.tar.gz"
    sudo cp geckodriver /usr/local/bin
    sudo pip install -U selenium==${GEM_SELENIUM_VERSION}

    cp $GEM_GIT_PACKAGE/openquake/moon/test/config/moon_config.py.tmpl $GEM_GIT_PACKAGE/openquake/moon/test/config/moon_config.py
    export DISPLAY=:1
    export PYTHONPATH=$HOME/$GEM_GIT_PACKAGE:$HOME/$GEM_GIT_PACKAGE/openquake/moon/test/config
    err=0
    python -m openquake.moon.nose_runner --failurecatcher dev -s -v -a '!negate' --with-xunit --xunit-file=xunit-moon-dev.xml $GEM_GIT_PACKAGE/openquake/moon/test || err=1
    for negate_file in screenshot_test; do
        beg_date="$(date "+%d/%b/%Y %H:%M:%S")"
        time_begin="$(date +%s%N)"
        python -m openquake.moon.nose_runner --failurecatcher dev-neg -s -v -a 'negate' --with-xunit --xunit-file=xunit-moon-dev-neg.xml "$GEM_GIT_PACKAGE/openquake/moon/test/${negate_file}.py" || true
        time_end="$(date +%s%N)"
        float_sec_time="$(echo "($time_end - $time_begin) / 1000000000" | bc -l | sed 's/\.\([0-9]\{3\}\).*$/.\1/g')"
        if [ ! -f  dev-neg_openquake.moon.test.*.${negate_file}.png ]; then
            echo "Expected file [dev-neg_openquake.moon.test.*.${negate_file}.png] not found"
            err=1
            break
        else
            rm xunit-moon-dev-neg.xml
            filename="$(ls dev-neg_openquake.moon.test.*.${negate_file}.png)"
            xml_out="$(echo "$filename" | sed 's/^[^\.]\+\.[^\.]\+\.[^\.]\+\.//g;s/\.png$//g;s/_/-/g;s/\./_/g').xml"
            cp "$GEM_GIT_PACKAGE/openquake/moon/test/xunit_tmpl/${xml_out}" "xunit-moon-dev_${xml_out}"
            sed -i "s@#DD/MM/YYYY HH:MM:SS#@$beg_date@g;s@#FLOAT_SEC_TIME#@$float_sec_time@g" "xunit-moon-dev_${xml_out}"
        fi
    done

    return $err
}

exec_test
