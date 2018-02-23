#!/bin/bash
#/*USE mysql;*/
#CREATE USER IF NOT EXISTS 'caliper'@'%' IDENTIFIED by '123456';
#insert into mysql.user(Host,User,Password) values("localhost","caliper",password("123456"));
mysql -u root -p << EOF
insert into mysql.user(Host,User,Password) values("localhost","caliper",password("123456"));
CREATE DATABASE IF NOT EXISTS caliper;
GRANT ALL ON caliper.* TO 'caliper'@'%';
FLUSH PRIVILEGES;
EOF
