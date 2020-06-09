import logging
import schedule
import time
import requests
import json
from multiprocessing import Process
from clients.gitlab_api import GitlabAPI

from server.config import Config

def job():
    log = logging.getLogger(__name__)
    log.info("Job started...")

    conf = Config().data

    recorder_url = conf['recorder_url']

    projectsc_host = conf['projectsc']['host']
    projectsc_token = conf['projectsc']['token']

    glapi = GitlabAPI(projectsc_host, projectsc_token)

    projects = glapi.get_all_projects()
    for project in projects:
        payload = {
            'project_id': project.id,
            'name': project.path,
            'namespace': project.namespace['path'],
            'default_branch': project.default_branch,
            'created_at': project.created_at,
            'last_activity_at': project.last_activity_at,
            'shared_with_groups_count': len(project.shared_with_groups),
            'statistics' : project.statistics
        }
        headers = {
            "Content-Type": "application/json"
        }
        r = requests.post("%s/api/v1/record/%s/%s" % (recorder_url, "code_sharing_projects", "projectsc"), data=json.dumps(payload), headers=headers)
        log.info("%s %d" % (payload['name'], r.status_code))

    # <class 'gitlab.v4.objects.Group'> => {'id': 5, 'web_url': 'https://projectscstg.popdata.bc.ca/groups/99-t05', 'name': '99-t05', 'path': '99-t05', 'description': '', 'visibility': 'private', 'share_with_group_lock': False, 'require_two_factor_authentication': False, 'two_factor_grace_period': 48, 'project_creation_level':'developer', 'auto_devops_enabled': None, 'subgroup_creation_level': 'owner', 'emails_disabled': None, 'mentions_disabled': None, 'lfs_enabled': True, 'default_branch_protection': 2, 'avatar_url': None, 'request_access_enabled': False, 'full_name': '99-t05', 'full_path': '99-t05', 'parent_id': None}
    groups = glapi.get_all_groups()
    for group in groups:
        #group = glapi.get_group_by_id (group_item.id)
        payload = {
            'group_id': group.id,
            'name': group.path
        }
        headers = {
            "Content-Type": "application/json"
        }
        r = requests.post("%s/api/v1/record/%s/%s" % (recorder_url, "code_sharing_groups", "projectsc"), data=json.dumps(payload), headers=headers)
        log.info("%s %d" % (payload['name'], r.status_code))

def sched():
    schedule.every().day.at("06:00").do(job)
    schedule.every().day.at("16:00").do(job)
    #schedule.every(10).seconds.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

def start():
    log = logging.getLogger(__name__)
    log.info("Starting schedule...")

    p = Process(target=sched, args=())
    p.start()

