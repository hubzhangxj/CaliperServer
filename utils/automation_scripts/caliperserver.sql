/*
Navicat MySQL Data Transfer

Source Server         : 192.168.64.97
Source Server Version : 50633
Source Host           : 192.168.64.97:3306
Source Database       : caliper

Target Server Type    : MYSQL
Target Server Version : 50633
File Encoding         : 65001

Date: 2017-12-28 17:24:38
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for auth_group
-- ----------------------------
DROP TABLE IF EXISTS `auth_group`;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for auth_group_permissions
-- ----------------------------
DROP TABLE IF EXISTS `auth_group_permissions`;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for auth_permission
-- ----------------------------
DROP TABLE IF EXISTS `auth_permission`;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=73 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for baseboard
-- ----------------------------
DROP TABLE IF EXISTS `baseboard`;
CREATE TABLE `baseboard` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `manufacturer` varchar(200) DEFAULT NULL,
  `version` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for cacheInfo
-- ----------------------------
DROP TABLE IF EXISTS `cacheInfo`;
CREATE TABLE `cacheInfo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `socketdes` varchar(255) DEFAULT NULL,
  `size` varchar(50) NOT NULL,
  `operational` varchar(255) DEFAULT NULL,
  `config_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `cacheInfo_config_id_7114012a_fk_config_id` (`config_id`),
  CONSTRAINT `cacheInfo_config_id_7114012a_fk_config_id` FOREIGN KEY (`config_id`) REFERENCES `config` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for caseResult
-- ----------------------------
DROP TABLE IF EXISTS `caseResult`;
CREATE TABLE `caseResult` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `result` double NOT NULL,
  `caseconfig` varchar(200) DEFAULT NULL,
  `unit` varchar(255) DEFAULT NULL,
  `case_id` int(11) NOT NULL,
  `sceResult_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `caseResult_case_id_516ddd1f_fk_testCase_id` (`case_id`),
  KEY `caseResult_sceResult_id_993e2f8a_fk_scenarioResult_id` (`sceResult_id`),
  CONSTRAINT `caseResult_case_id_516ddd1f_fk_testCase_id` FOREIGN KEY (`case_id`) REFERENCES `testCase` (`id`),
  CONSTRAINT `caseResult_sceResult_id_993e2f8a_fk_scenarioResult_id` FOREIGN KEY (`sceResult_id`) REFERENCES `scenarioResult` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3006 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for config
-- ----------------------------
DROP TABLE IF EXISTS `config`;
CREATE TABLE `config` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(50) DEFAULT NULL,
  `kernel` varchar(50) DEFAULT NULL,
  `os` varchar(50) DEFAULT NULL,
  `board_id` int(11) NOT NULL,
  `sys_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `config_board_id_e56be651_fk_baseboard_id` (`board_id`),
  KEY `config_sys_id_69257c53_fk_system_id` (`sys_id`),
  CONSTRAINT `config_board_id_e56be651_fk_baseboard_id` FOREIGN KEY (`board_id`) REFERENCES `baseboard` (`id`),
  CONSTRAINT `config_sys_id_69257c53_fk_system_id` FOREIGN KEY (`sys_id`) REFERENCES `system` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for cpu
-- ----------------------------
DROP TABLE IF EXISTS `cpu`;
CREATE TABLE `cpu` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `socketdes` varchar(50) DEFAULT NULL,
  `manufacturer` varchar(50) DEFAULT NULL,
  `version` varchar(50) DEFAULT NULL,
  `maxspeed` varchar(50) DEFAULT NULL,
  `currentspeed` varchar(50) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `corecount` int(11) NOT NULL,
  `enabledCore` int(11) NOT NULL,
  `threadcount` int(11) NOT NULL,
  `config_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `cpu_config_id_e1f701d8_fk_config_id` (`config_id`),
  CONSTRAINT `cpu_config_id_e1f701d8_fk_config_id` FOREIGN KEY (`config_id`) REFERENCES `config` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for dimension
-- ----------------------------
DROP TABLE IF EXISTS `dimension`;
CREATE TABLE `dimension` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `desc` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for dimResult
-- ----------------------------
DROP TABLE IF EXISTS `dimResult`;
CREATE TABLE `dimResult` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `result` double NOT NULL,
  `dim_id` int(11) NOT NULL,
  `task_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dimResult_dim_id_8ae0182e_fk_dimension_id` (`dim_id`),
  KEY `dimResult_task_id_8d13bdc2_fk_task_id` (`task_id`),
  CONSTRAINT `dimResult_dim_id_8ae0182e_fk_dimension_id` FOREIGN KEY (`dim_id`) REFERENCES `dimension` (`id`),
  CONSTRAINT `dimResult_task_id_8d13bdc2_fk_task_id` FOREIGN KEY (`task_id`) REFERENCES `task` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=78 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for django_admin_log
-- ----------------------------
DROP TABLE IF EXISTS `django_admin_log`;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_userProfile_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_userProfile_id` FOREIGN KEY (`user_id`) REFERENCES `userProfile` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for django_content_type
-- ----------------------------
DROP TABLE IF EXISTS `django_content_type`;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for django_migrations
-- ----------------------------
DROP TABLE IF EXISTS `django_migrations`;
CREATE TABLE `django_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for django_session
-- ----------------------------
DROP TABLE IF EXISTS `django_session`;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for log
-- ----------------------------
DROP TABLE IF EXISTS `log`;
CREATE TABLE `log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content` longtext,
  `task_id` int(11) NOT NULL,
  `tool_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `log_task_id_d5645ad9_fk_task_id` (`task_id`),
  KEY `log_tool_id_77d31c27_fk_testTool_id` (`tool_id`),
  CONSTRAINT `log_task_id_d5645ad9_fk_task_id` FOREIGN KEY (`task_id`) REFERENCES `task` (`id`),
  CONSTRAINT `log_tool_id_77d31c27_fk_testTool_id` FOREIGN KEY (`tool_id`) REFERENCES `testTool` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=98 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for memory
-- ----------------------------
DROP TABLE IF EXISTS `memory`;
CREATE TABLE `memory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `manufacturer` varchar(255) DEFAULT NULL,
  `size` varchar(50) DEFAULT NULL,
  `type` varchar(50) DEFAULT NULL,
  `speed` varchar(50) DEFAULT NULL,
  `clockspeed` varchar(50) DEFAULT NULL,
  `banklocator` varchar(50) DEFAULT NULL,
  `config_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `memory_config_id_ca2e2a37_fk_config_id` (`config_id`),
  CONSTRAINT `memory_config_id_ca2e2a37_fk_config_id` FOREIGN KEY (`config_id`) REFERENCES `config` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for net
-- ----------------------------
DROP TABLE IF EXISTS `net`;
CREATE TABLE `net` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `interface` varchar(50) DEFAULT NULL,
  `bandwidth` varchar(50) DEFAULT NULL,
  `driver` varchar(50) DEFAULT NULL,
  `driverversion` varchar(50) DEFAULT NULL,
  `protocoltype` varchar(50) DEFAULT NULL,
  `address` varchar(50) DEFAULT NULL,
  `broadcast` varchar(50) DEFAULT NULL,
  `netmask` varchar(50) DEFAULT NULL,
  `network` varchar(50) DEFAULT NULL,
  `mac` varchar(50) DEFAULT NULL,
  `config_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `net_config_id_b6bc4b74_fk_config_id` (`config_id`),
  CONSTRAINT `net_config_id_b6bc4b74_fk_config_id` FOREIGN KEY (`config_id`) REFERENCES `config` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for partition
-- ----------------------------
DROP TABLE IF EXISTS `partition`;
CREATE TABLE `partition` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `size` varchar(50) DEFAULT NULL,
  `storage_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `partition_storage_id_66dac072_fk_storage_id` (`storage_id`),
  CONSTRAINT `partition_storage_id_66dac072_fk_storage_id` FOREIGN KEY (`storage_id`) REFERENCES `storage` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for scenario
-- ----------------------------
DROP TABLE IF EXISTS `scenario`;
CREATE TABLE `scenario` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `desc` varchar(200) DEFAULT NULL,
  `parentid` int(11) NOT NULL,
  `dim_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `scenario_dim_id_fdde1eda_fk_dimension_id` (`dim_id`),
  CONSTRAINT `scenario_dim_id_fdde1eda_fk_dimension_id` FOREIGN KEY (`dim_id`) REFERENCES `dimension` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for scenarioResult
-- ----------------------------
DROP TABLE IF EXISTS `scenarioResult`;
CREATE TABLE `scenarioResult` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `result` double NOT NULL,
  `dimresult_id` int(11) NOT NULL,
  `scenario_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `scenarioResult_dimresult_id_5f29b947_fk_dimResult_id` (`dimresult_id`),
  KEY `scenarioResult_scenario_id_10c6a1d1_fk_scenario_id` (`scenario_id`),
  CONSTRAINT `scenarioResult_dimresult_id_5f29b947_fk_dimResult_id` FOREIGN KEY (`dimresult_id`) REFERENCES `dimResult` (`id`),
  CONSTRAINT `scenarioResult_scenario_id_10c6a1d1_fk_scenario_id` FOREIGN KEY (`scenario_id`) REFERENCES `scenario` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=360 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for storage
-- ----------------------------
DROP TABLE IF EXISTS `storage`;
CREATE TABLE `storage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `devicename` varchar(50) DEFAULT NULL,
  `manufactor` varchar(50) DEFAULT NULL,
  `capacity` varchar(50) DEFAULT NULL,
  `sectorsize` varchar(50) DEFAULT NULL,
  `config_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `storage_config_id_29ddf104_fk_config_id` (`config_id`),
  CONSTRAINT `storage_config_id_29ddf104_fk_config_id` FOREIGN KEY (`config_id`) REFERENCES `config` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for system
-- ----------------------------
DROP TABLE IF EXISTS `system`;
CREATE TABLE `system` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `manufacturer` varchar(200) DEFAULT NULL,
  `version` varchar(50) DEFAULT NULL,
  `productname` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for task
-- ----------------------------
DROP TABLE IF EXISTS `task`;
CREATE TABLE `task` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `time` datetime(6) DEFAULT NULL,
  `remark` varchar(50) DEFAULT NULL,
  `delete` tinyint(1) NOT NULL,
  `name` varchar(50) NOT NULL,
  `config_id` int(11) NOT NULL,
  `owner_id` int(11) NOT NULL,
  `path` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `task_config_id_0162b8cf_fk_config_id` (`config_id`),
  KEY `task_owner_id_61ef33dc_fk_userProfile_id` (`owner_id`),
  CONSTRAINT `task_config_id_0162b8cf_fk_config_id` FOREIGN KEY (`config_id`) REFERENCES `config` (`id`),
  CONSTRAINT `task_owner_id_61ef33dc_fk_userProfile_id` FOREIGN KEY (`owner_id`) REFERENCES `userProfile` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for task_shareusers
-- ----------------------------
DROP TABLE IF EXISTS `task_shareusers`;
CREATE TABLE `task_shareusers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_id` int(11) NOT NULL,
  `userprofile_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_shareusers_task_id_userprofile_id_4298d70d_uniq` (`task_id`,`userprofile_id`),
  KEY `task_shareusers_userprofile_id_a086c99b_fk_userProfile_id` (`userprofile_id`),
  CONSTRAINT `task_shareusers_task_id_873b70d9_fk_task_id` FOREIGN KEY (`task_id`) REFERENCES `task` (`id`),
  CONSTRAINT `task_shareusers_userprofile_id_a086c99b_fk_userProfile_id` FOREIGN KEY (`userprofile_id`) REFERENCES `userProfile` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for testCase
-- ----------------------------
DROP TABLE IF EXISTS `testCase`;
CREATE TABLE `testCase` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `desc` varchar(200) DEFAULT NULL,
  `scenario_id` int(11) NOT NULL,
  `tool_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `testCase_scenario_id_052aefce_fk_scenario_id` (`scenario_id`),
  KEY `testCase_tool_id_11f90b06_fk_testTool_id` (`tool_id`),
  CONSTRAINT `testCase_scenario_id_052aefce_fk_scenario_id` FOREIGN KEY (`scenario_id`) REFERENCES `scenario` (`id`),
  CONSTRAINT `testCase_tool_id_11f90b06_fk_testTool_id` FOREIGN KEY (`tool_id`) REFERENCES `testTool` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=334 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for testTool
-- ----------------------------
DROP TABLE IF EXISTS `testTool`;
CREATE TABLE `testTool` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `desc` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for userProfile
-- ----------------------------
DROP TABLE IF EXISTS `userProfile`;
CREATE TABLE `userProfile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(30) NOT NULL,
  `last_name` varchar(30) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `avatar` varchar(100) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `role` int(11) NOT NULL,
  `company` varchar(255) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `telphone` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for userProfile_groups
-- ----------------------------
DROP TABLE IF EXISTS `userProfile_groups`;
CREATE TABLE `userProfile_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `userprofile_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `userProfile_groups_userprofile_id_group_id_513f5347_uniq` (`userprofile_id`,`group_id`),
  KEY `userProfile_groups_group_id_7676dfa7_fk_auth_group_id` (`group_id`),
  CONSTRAINT `userProfile_groups_group_id_7676dfa7_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `userProfile_groups_userprofile_id_49849448_fk_userProfile_id` FOREIGN KEY (`userprofile_id`) REFERENCES `userProfile` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for userProfile_user_permissions
-- ----------------------------
DROP TABLE IF EXISTS `userProfile_user_permissions`;
CREATE TABLE `userProfile_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `userprofile_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `userProfile_user_permiss_userprofile_id_permissio_61137c36_uniq` (`userprofile_id`,`permission_id`),
  KEY `userProfile_user_per_permission_id_f0981587_fk_auth_perm` (`permission_id`),
  CONSTRAINT `userProfile_user_per_permission_id_f0981587_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `userProfile_user_per_userprofile_id_42095003_fk_userProfi` FOREIGN KEY (`userprofile_id`) REFERENCES `userProfile` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
SET FOREIGN_KEY_CHECKS=1;
