#!/bin/bash

BRANCH_ID="$1"

: ${GECKODRIVER_VER:=0.16.1}
: ${SELENIUM_VER:=3.4.1}
export GECKODRIVER_VER SELENIUM_VER

#display each command before executing it
set -x
. .gem_init.sh

#apt-get update/upgrade
sudo apt-get -y update
sudo apt-get -y upgrade

#function complete procedure for tests
exec_test () {    
    #install selenium,pip,geckodriver,clone oq-moon and execute tests with nose 
    sudo apt-get -y install python-pip
    sudo pip install --upgrade pip
    sudo pip install nose
    sudo pip install -U selenium==${SELENIUM_VER}
    # wget http://ftp.openquake.org/mirror/mozilla/geckodriver-latest-linux64.tar.gz

    wget "http://ftp.openquake.org/mirror/mozilla/geckodriver-v${GECKODRIVER_VER}-linux64.tar.gz"
    tar zxvf "geckodriver-v${GECKODRIVER_VER}-linux64.tar.gz"
    sudo cp geckodriver /usr/local/bin
    
    cp $GEM_GIT_PACKAGE/openquake/moon/test/config/moon_config.py.tmpl $GEM_GIT_PACKAGE/openquake/moon/test/config/moon_config.py
    export DISPLAY=:1
    export PYTHONPATH=$GEM_GIT_PACKAGE:$GEM_GIT_PACKAGE/openquake/moon/test/config
    cd $GEM_GIT_PACKAGE
    python -m openquake.moon.nose_runner --failurecatcher dev -s -v --with-xunit --xunit-file=xunit-platform-dev.xml $GEM_GIT_PACKAGE/openquake/moon/test || true
    # sleep 40000 || true
}

exec_test
