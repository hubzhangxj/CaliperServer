insert into mysql.user(Host,User,Password) values("%","caliper",password("123456"));
CREATE DATABASE IF NOT EXISTS caliper;
GRANT ALL ON caliper.* TO 'caliper'@'%';
UPDATE mysql.user SET Password=PASSWORD('root') WHERE User='root';
FLUSH PRIVILEGES;

