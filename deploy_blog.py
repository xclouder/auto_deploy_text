#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from fabric.state import env
from fabric.api import run
from fabric.api import cd
from fabric.contrib.files import exists


def set_hosts():
    env.user = 'deploy'
    env.hosts = ['103.192.178.32:36957']
    env.passwords = {'deploy@103.192.178.32:36957':'learntolive'}

def deploy(directory, program_name, program_git_branch=None, program_git_branch_rev=None, program_numproces_start=1, program_numproces=4, 
            program_start_interval=1, supervisord_bin_path='/data/py_crazy_env/bin', supervisord_conf_file="/etc/supervisord.conf"):
    """部署指定的应用。
    Args:
        directory：应用所在目录，该目录有完整的buildout支持
        program_name：应用在supervisor中配置的名称
        program_git_branch：应用源文件对应的git分支名称,默认为master(与program_git_branch_rev设置互斥)
        program_git_branch_rev: 应用源文件对应的git分支版本,默认为HEAD(与program_git_branch设置互斥)
        program_numproces_start：重启应用时传递给supervior的起始进程编号
        program_numproces：重启应用的进程数量
        program_start_interval：重启进程之间的间隔时间
        supervisord_bin_path：supervisor命令所在路径
        supervisord_conf_file：supervisord的配置文件
    """

    if not exists(directory):
        raise Exception(u"Not Found {0}".format(directory))

    program_numproces_start = int(program_numproces_start)
    program_numproces = int(program_numproces)
    program_start_interval = int(program_start_interval)
    
    with(cd(directory)):
        run("export PATH={0}:$PATH".format(supervisord_bin_path))
        # 设置git需要拉取的分支或者版本
        # Note that the branch and rev option are mutually exclusive.
        run("echo '[app_branch]' > app_branch.cfg")
        run("echo 'cmd_options = {0}' >> app_branch.cfg".format(
            "branch={0}".format(program_git_branch) if program_git_branch else "rev={0}".format(program_git_branch_rev or "HEAD")))
        
        # 执行构建
        run("bin/buildout -Nv")
        # 更新supervisor的配置文件
        run("supervisorctl -c {0} update".format(supervisord_conf_file))
        # 开始逐个启动关闭应用进程
        run_supervisorctl_with_program = lambda cmd, program_num: run(
            "supervisorctl -c {supervisord_conf} {cmd} {program_name}:{program_name}{process_num}".format(
                supervisord_conf=supervisord_conf_file,
                program_name=program_name,
                process_num=program_num,
                cmd=cmd))
        for program_num in range(program_numproces_start, program_numproces_start + program_numproces):
            run_supervisorctl_with_program("stop", program_num)
            run_supervisorctl_with_program("start", program_num)
            run("sleep {0}".format(program_start_interval))

def my_deploy():
    run ("touch deploy.log")
