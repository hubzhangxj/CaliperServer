#!/bin/bash
## How to build caliperserver.install:
# tar cvzf caliperserver-[ver].tar.gz CaliperServer 
# cat caliperserver.install caliperserver-[ver].tar.gz > caliperserver-[ver].install
ARCHIVE=`awk '/^__ARCHIVE_BELOW__/ {print NR+1; exit 0}' "$0"`

env_config="/tmp/CaliperServer/utils/automation_scripts/environment.config"
depend_json="/tmp/CaliperServer/utils/automation_scripts/dependency.json" 

## main 
main()
{

##	1. check user

    user=`whoami`
    if [ "$user" = "root" ]
    then
        echo "Please run this program as normal user!"
	exit 0
    fi

##         check whiptail
    which whiptail
    ret=$?
    if [ $ret -ne 0 ]
    then
        echo "Install whiptail..."

        system_os=`cat /etc/os-release | grep -owP 'ID=\K\S+' | sed 's/"//g'`
        case $system_os in
        ubuntu)
            sudo apt install -y whiptail
            ;;
        centos|rhel)
            sudo yum install -y newt
            ;;
        sles)
            sudo zypper --no-gpg-checks  install -y http://mirror.centos.org/altarch/7/os/aarch64/Packages/newt-0.52.15-4.el7.aarch64.rpm
            ;;
        esac
    fi

    which whiptail
    ret=$?
    if [ $ret -ne 0 ]
    then
        echo "Please install whiptail first, then run this program again!"
        exit 0
    fi

##	2. tar source code to /tmp

    tail -n+$ARCHIVE "$0" | tar xzm -C /tmp

    if [ ! -d /tmp/CaliperServer ]; then
	whiptail --title "Error" --msgbox "Could not find install file. exit" 9 50
	exit 1	
    fi

    . /tmp/CaliperServer/utils/automation_scripts/install_functions

##	3. create log file
   
    log="$HOME/caliperserver_output/install_"$(date +%Y-%m-%d_%H-%M-%S)".log"
    if [ ! -d $HOME/caliperserver_output ]; then 
	mkdir -p $HOME/caliperserver_output
    fi
    if [ ! -f $log ]
    then 
        touch $log
    fi
    sudo chown $user:$user $log

##	4. write the new version number to the log file 
    
    new_version=`cat /tmp/CaliperServer/common.py | grep -owP "VERSION=\K\S+" | sed 's/\"//g'`
    write_log "[caliperserver]" $log
    write_log "version=$new_version" $log 

    system_os=`cat /etc/os-release | grep -owP 'ID=\K\S+' | sed 's/"//g'`
    system_os_version=`cat /etc/os-release | grep -owP 'VERSION_ID=\K\S+' | sed 's/"//g'`
    system_arch=`uname -m`
    system_processor_manufacturer=`sudo dmidecode --string processor-manufacturer`
    system_processor_version=`sudo dmidecode --string processor-version`

    write_log "[system_information]" $log
    write_log "os=$system_os" $log
    write_log "os_version=$system_os_version" $log
    write_log "arch=$system_arch" $log
    write_log "processor_manfacturer=$system_processor_manufacturer" $log
    write_log "processor_version=$system_processor_version" $log

##	5. check OS soft information
    {
	check_osinfo $env_config
	ret=$?
    	if [ $ret -ne 0 ]; then
	    write_log "Fail! The OS $system_os $system_os_version is not supported. $ret" $log
	    echo "Fail! The OS $system_os $system_os_version is not supported. $ret" 
	fi
    } | whiptail --title "CaliperServer installation" --gauge "Check if the OS is supported" 7 55 0

    tail -1 $log | grep "^Fail! The OS"
    if [ $? -eq 0 ]
    then
	#write_log "Fail! The OS $system_os $system_os_version is not supported ..." $log
        show_message "Fail! The OS $system_os $system_os_version is not supported." 7 50 
	exit 5
    fi 
 
## 	6. check hardware platform 

    {
	check_hardinfo $env_config
	ret=$?
    	if [ $ret -ne 0 ]
    	then
            write_log "Fail! The Processor $system_processor_version is not supported." $log
	fi
    } | whiptail --title "CaliperServer installation" --gauge "Check if the hardware platform is supported" 7 55 3

    tail -1 $log | grep "^Fail! The Processor"
    if [ $? -eq 0 ]
    then
        #write_log "Fail! The Processor $system_processor_version is not supported ..." $log
        show_message "Fail! The Processor $system_processor_version is not supported." 9 50 
	exit 6
    fi 
 
## 	7. check if the network is connected
    {
	check_net $env_config
	ret=$?
        if [ $ret -ne 0 ]
	then
            write_log "Fail! The network is down ..." $log
	fi
    } | whiptail --title "CaliperServer installation" --gauge "Check if the network is connected" 7 55 7

    tail -1 $log | grep "^Fail! The network"
    if [ $? -eq 0 ]
    then
        #write_log "Fail! The network is down ..." $log
        show_message "Fail! The network is down ..." 9 50 
	exit 7
    fi 
 
## 	8. check version
    {
	check_version $new_version
	ret=$?
        if [ $ret -eq 2 ]
	then
	    write_log "Fail! Newer or same version of caliperserver already installed" $log
	fi
    } | whiptail --title "CaliperServer installation" --gauge "Check if $new_version is newer than installed version" 7 55 8

    tail -1 $log | grep "^Fail! Newer"
    if [ $? -eq 0 ]
    then
	show_message "Fail! Newer or same version of caliperserver already installed. " 9 50
	exit
    fi

## 9. write install date

    log_install_date

## 10. install jq package
    case $system_os in
    ubuntu)
	pkg_type="dpk"
        order="apt-get"
	;;
    centos|rhel)
	pkg_type="rpm"
        order="yum"
	;;
    sles)
        pkg_type="rpm"
        order="zypper"
    esac

    {
    case $order in
    apt-get)
	sudo apt-get update > /tmp/caliperserver_tmp.log 2>&1
	;;
    yum)
	sudo yum update -y > /tmp/caliperserver_tmp.log 2>&1
	;;
    zypper)
	sudo zypper update -y > /tmp/caliperserver_tmp.log 2>&1
	;;
    esac
    } | whiptail --title "CaliperServer installation" --gauge "Updating software info " 7 55 10

    write_log "[install_jq]" $log
    {
        install_pkg jq $pkg_type $order
        ret=$?
        case $ret in
        0)
    	    write_log "jq pkg install success" $log
    	    ;;
        1)
    	    write_log "jq pkg install already" $log
    	    ;;
        2)
    	    write_log "jq pkg install failed" $log
            show_message "install jq failed. Exit install" 7 45 
    	    exit 10
    	    ;;
        esac
    } | whiptail --title "CaliperServer installation" --gauge "jq" 7 55 12
  
    write_log "[install_bc]" $log
    {
        install_pkg bc $pkg_type $order
        ret=$?
        case $ret in
        0)
    	    write_log "bc pkg install success" $log
    	    ;;
        1)
    	    write_log "bc pkg install already" $log
    	    ;;
        2)
    	    write_log "bc pkg install failed" $log
            show_message "install bc failed. Exit install" 7 45 
    	    exit 11
    	    ;;
        esac
    } | whiptail --title "CaliperServer installation" --gauge "bc" 7 55 13

## 11. install dpkg or rpm packages

    write_log "[install_pkg]" $log
    install_all_pkg 

## 12. install pip packages

    write_log "[install_pip]" $log
    install_all_pip

## 13. copy uninstall.sh to $HOME/caliperserver_output and copy code to /opt
   
    write_log "[install_caliperserver]" $log 
    {
        if [ ! -f $HOME/caliperserver_output/uninstall.sh ]
        then
            sudo cp /tmp/CaliperServer/utils/automation_scripts/uninstall.sh $HOME/caliperserver_output/
        else 
            sudo rm $HOME/caliperserver_output/uninstall.sh
            sudo cp /tmp/CaliperServer/utils/automation_scripts/uninstall.sh $HOME/caliperserver_output/
        fi
        if [ ! -d /opt/CaliperServer ]
        then 
            sudo cp -r /tmp/CaliperServer /opt/
        else 
            sudo rm -rf /opt/CaliperServer
            sudo cp -r /tmp/CaliperServer /opt/
        fi
        
        write_log "caliperserver install success" $log

    } | whiptail --title "CaliperServer installation" --gauge "caliperserver" 7 55 95

## 14. finish
    show_message "install caliperserver successed." 9 50

## 15. config sql and config nginx and start nginx service
    config_mysql
   
    config_nginx

#    start_nginx

    exit 0

}

main

__ARCHIVE_BELOW__
