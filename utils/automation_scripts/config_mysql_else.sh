#!/bin/bash
#/*USE mysql;*/
mysql -u root -p <<EOF
CREATE USER 'caliper'@'%' IDENTIFIED by '123456';
CREATE DATABASE IF NOT EXISTS caliper;
GRANT ALL ON caliper.* TO 'caliper'@'%';
FLUSH PRIVILEGES;
EOF

#run_init_sql caliperserver.sql
mysql -ucaliper -p123456 -Dcaliper < /opt/CaliperServer/utils/automation_scripts/caliperserver.sql
echo $?
