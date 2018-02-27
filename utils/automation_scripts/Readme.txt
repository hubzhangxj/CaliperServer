***********************************************
** How to make caliperserver install package **
***********************************************

1 Get caliperserver source code by git clone

  $ git clone https://github.com/TSestuary/caliperserver

2 (optional) Modify software version by modify
  caliperserver/common.py. The keyword is VERSION

  VERSION="0.0.7"  

3 Run the script caliperserver_package.sh to build the 
  install package

  $ cd caliperserver/utils/automation_scripts
  $ ./caliperserver_package.sh

  The install package will be $HOME/caliperserver-$VERSION.install,
  and the md5 file will generated.

