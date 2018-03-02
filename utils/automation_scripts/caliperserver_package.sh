#!/bin/bash
## How to build caliper_[var].install

#check user
user=`whoami`
if [ "$user" = 'root' ]; then
    echo "Please run this program as a normal user!"
    exit 0
fi

cd `dirname $0` 
 
tar cvzf $HOME/caliperserver.tar.gz ../../../CaliperServer --exclude=.git

var=`cat ../../common.py | grep -owP "VERSION=\K\S+" | sed 's/\"//g'`

cat install.sh $HOME/caliperserver.tar.gz > $HOME/caliperserver-$var.install

md5sum $HOME/caliperserver-$var.install > $HOME/caliperserver-$var.install.md5

chmod 775 $HOME/caliperserver-$var.install

rm -f caliperserver.tar.gz
rm -f $HOME/caliperserver-v$var.zip

cd $HOME && zip caliperserver-v$var.zip caliperserver-$var.install caliperserver-$var.install.md5

