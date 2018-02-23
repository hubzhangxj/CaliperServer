#run_init_sql init.sql
sudo mysql --defaults-file=/etc/mysql/debian.cnf < /opt/CaliperServer/utils/automation_scripts/init.sql
echo $?

#run_init_sql caliperserver.sql
mysql -ucaliper -p123456 -Dcaliper < /opt/CaliperServer/utils/automation_scripts/caliperserver.sql
echo $?
