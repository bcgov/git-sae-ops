import gitlab

from gitlab.exceptions import GitlabError, GitlabCreateError

import logging
log = logging.getLogger(__name__)

class GitlabAPI():
    def __init__(self, host, token):
        self.gl = gitlab.Gitlab(host, private_token=token)

    def update_root_create_groups(self):
        log.info('{0:30}'.format('update_root_create_groups'))

        user = self.gl.users.list(username='root')[0]
        user.can_create_group = 1 
        user.save()

    def get_all_groups(self):
        log.info('{0:30}'.format('get_all_groups'))
        return self.gl.groups.list(all=True, retry_transient_errors=True)

    def get_group(self, aGroup):
        log.info('{0:30} {1}'.format('get_group', aGroup))
        groups = self.gl.groups.list(search=aGroup, retry_transient_errors=True)
        for group in groups:
            if group.name == aGroup:
                log.info('{0:30} {1} id:{2}'.format('', aGroup, group.id))
                return group
        raise Exception("Group %s not found" % aGroup)

    def create_get_group(self, aGroup):
        log.info('{0:30} {1}'.format('create_get_group', aGroup))
        groups = self.gl.groups.list(search=aGroup, retry_transient_errors=True)
        for group in groups:
            if group.name == aGroup:
                log.info('{0:30} {1} id:{2}'.format('', aGroup, group.id))
                return group.id
        log.info('{0:30} {1} CREATING'.format('', aGroup))
        group = self.gl.groups.create({'name':aGroup, 'path':aGroup, 'visibility':'private'}, retry_transient_errors=True)
        log.info('{0:30} {1} id:{2}'.format('', aGroup, group.id))
        return group.id

    def create_get_project(self, aNamespaceId, aProject):
        log.info('{0:30} {1} in group:{2}'.format('create_get_project', aProject, aNamespaceId))
        projects = self.gl.projects.list(search=aProject, retry_transient_errors=True)
        for project in projects:
            if project.name == aProject and project.namespace['id'] == aNamespaceId:
                return project.id
        log.info('{0:30} {1} CREATING'.format('', aProject))
        project = self.gl.projects.create({'name':aProject, 'namespace_id':aNamespaceId, 'initialize_with_readme':False}, retry_transient_errors=True)
        return project.id

    def import_get_project(self, aNamespaceId, aProject, aUrl):
        log.info('{0:30} {1} URL {2}'.format('import_get_project', aProject, aUrl))
        projects = self.gl.projects.list(search=aProject, retry_transient_errors=True)
        for project in projects:
            if project.name == aProject and project.namespace['id'] == aNamespaceId:
                return project.id
        log.info('{0:30} {1} IMPORTING'.format('', aProject))
        project = self.gl.projects.create({'name':aProject, 'path':aProject, 'namespace_id':aNamespaceId, 'import_url':aUrl})
        return project.id

    def set_custom_attribute (self, aProjectId, key, value):
        log.info('{0:30} {1} : {2} = {3}'.format('set_custom_attribute', aProjectId, key, value))

        project = self.gl.projects.get(aProjectId)
        project.customattributes.set(key, value)

    def get_custom_attribute (self, aProjectId, key):
        log.info('{0:30} {1} : {2}'.format('get_custom_attribute', aProjectId, key))
        project = self.gl.projects.get(aProjectId)
        attr = project.customattributes.get(key)
        log.info('{0:30} {1} : {2} = {3}'.format('', aProjectId, key, attr.value))
        return attr.value

    def config_project_variant1(self, aProjectId):
        log.info('{0:30} {1} : {2}'.format('config_project', aProjectId, "jobs_enabled"))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)
        if project.jobs_enabled == False:
            project.jobs_enabled = True
        project.repository_enabled = True
        project.issues_enabled = True
        project.wiki_enabled = False
        project.snippets_enabled = False
        project.public_jobs = False
        project.lfs_enabled = False
        project.only_allow_merge_if_pipeline_succeeds = True
        project.only_allow_merge_if_all_discussions_are_resolved = True
        project.save(retry_transient_errors=True)

    def config_project_variant2(self, aProjectId):
        log.info('{0:30} {1} : {2}'.format('config_project', aProjectId, "jobs_enabled,issues_disabled,wiki_disabled"))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)
        if project.jobs_enabled == False:
            project.jobs_enabled = True
        project.repository_enabled = True
        project.issues_enabled = False
        project.wiki_enabled = False
        project.snippets_enabled = False
        project.public_jobs = False
        project.lfs_enabled = False
        project.only_allow_merge_if_pipeline_succeeds = True
        project.only_allow_merge_if_all_discussions_are_resolved = True
        # project.auto_devops_attributes = { enabled : False }
        project.save(retry_transient_errors=True)

    def config_project_variant_shared(self, aProjectId):
        log.info('{0:30} {1} : {2}'.format('config_project', aProjectId, "jobs_enabled,issued_disabled,wiki_disabled"))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)
        project.jobs_enabled = False
        project.repository_enabled = True
        project.issues_enabled = False
        project.wiki_enabled = False
        project.snippets_enabled = False
        project.public_jobs = False
        project.lfs_enabled = False
        project.only_allow_merge_if_pipeline_succeeds = False
        project.only_allow_merge_if_all_discussions_are_resolved = False
        project.save(retry_transient_errors=True)

    def config_project_variant_private(self, aProjectId):
        log.info('{0:30} {1} : {2}'.format('config_project', aProjectId, "jobs_enabled,issued_enabled,wiki_enabled"))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)
        project.jobs_enabled = False
        project.repository_enabled = True
        project.issues_enabled = True
        project.wiki_enabled = True
        project.snippets_enabled = False
        project.public_jobs = False
        project.lfs_enabled = False
        project.only_allow_merge_if_pipeline_succeeds = False
        project.only_allow_merge_if_all_discussions_are_resolved = False
        project.save(retry_transient_errors=True)

    def approve_merge (self, mr):

        log.info('{0:30} id={1} [{2}] {3}'.format('approve_merge', mr.id, mr.state, mr.title))

        try:
            mr.merge()
        except GitlabError as err:
            if (err.response_code == 405):
                raise Exception("Merge request can not be merged.  Check that the MR has met all required criteria.")
            else:
                raise Exception("Unexpected error from Gitlab")

    def delete_merge (self, mr):

        log.info('{0:30} id={1} [{2}] {3}'.format('delete_merge', mr.id, mr.state, mr.title))

        mr.delete()

    def close_merge (self, mr):

        log.info('{0:30} id={1} [{2}] {3}'.format('close_merge', mr.id, mr.state, mr.title))

        mr.state_event = 'close'
        mr.save()

    def get_merge_request(self, aProjectId, sourceBranch, targetBranch, targetProjectId, labels):
        log.info('{0:30} {1} {2} --> {3}'.format('get_merge_request', aProjectId, sourceBranch, targetBranch))

        if targetProjectId is not None:
            for mr in self.gl.projects.get(targetProjectId).mergerequests.list():
                if mr.source_branch == sourceBranch and mr.target_branch == targetBranch and (mr.state != 'closed' and mr.state != 'merged'):
                    return mr

        project = self.gl.projects.get(aProjectId)
        mrs = project.mergerequests.list()
        for mr in mrs:
            # log.info('{0:30} Merge Request? {1} {2} {3}'.format('', mr.source_branch, mr.target_branch, mr.state))
            if mr.source_branch == sourceBranch and mr.target_branch == targetBranch and (mr.state != 'closed' and mr.state != 'merged'):
                return mr

        log.info('{0:30} {1}'.format('', ': MERGE NOT FOUND'))
        return None

    def create_get_merge_request(self, aProjectId, title, sourceBranch, targetBranch, targetProjectId, labels):
        mr = self.get_merge_request(aProjectId, sourceBranch, targetBranch, targetProjectId, labels)
        if mr is None:
            return self.create_merge_request(aProjectId, title, sourceBranch, targetBranch, targetProjectId, labels)
        else:
            return mr

    def create_merge_request(self, aProjectId, title, sourceBranch, targetBranch, targetProjectId, labels):
        log.info('{0:30} {1} {2} : {3} --> {4}'.format('create_merge_request', aProjectId, title, sourceBranch, targetBranch))

        project = self.gl.projects.get(aProjectId)

        log.info('{0:30} {1} {2} CREATING'.format('', aProjectId, title))
        mr = project.mergerequests.create({'source_branch': sourceBranch,
                                   'target_project_id': targetProjectId,
                                   'target_branch': targetBranch,
                                   'title': title,
                                   'labels': labels})
        return mr

    def create_get_branch(self, aNamespaceId, aProject, aBranch, ref = 'master', attempt = 0):
        log.info('{0:30} {1} {2}'.format('create_get_branch', aProject, aBranch))
        projects = self.gl.projects.list(search=aProject, retry_transient_errors=True)
        for project in projects:
            if project.name == aProject and project.namespace['id'] == aNamespaceId:
                branches = project.branches.list(retry_transient_errors=True)
                for branch in branches:
                    if branch.name == aBranch:
                        return branch.name

                log.info('{0:30} {1} CREATING'.format('', aBranch))

                create_params = {'branch': aBranch}
                if ref is not None:
                    create_params['ref'] = ref
                try:
                    branch = project.branches.create(create_params)
                except GitlabCreateError as err:
                    if err.response_code == 502 and attempt == 0:
                        log.info('{0:30} {1} FAILED WITH 502 - try again'.format('', aBranch))
                        return self.create_get_branch(aNamespaceId, aProject, aBranch, ref, attempt + 1)
                    else:
                        raise err
                return aBranch
        raise Exception("Project %s in %s not found" % (aProject, aNamespaceId))

    def set_default_branch(self, aNamespaceId, aProject, aBranch):
        log.info('{0:30} {1} {2}'.format('set_default_branch', aProject, aBranch))
        projects = self.gl.projects.list(search=aProject, retry_transient_errors=True)
        for project in projects:
            if project.name == aProject and project.namespace['id'] == aNamespaceId:
                project.default_branch = aBranch
                project.save(retry_transient_errors=True)
                return
        raise Exception("Project %s in %s not found" % (aProject, aNamespaceId))

    def has_branch (self, aNamespaceId, aProject, aBranch):
        log.info('{0:30} {1} {2}'.format('has_branch', aProject, aBranch))
        projects = self.gl.projects.list(search=aProject, retry_transient_errors=True)
        for project in projects:
            if project.name == aProject and project.namespace['id'] == aNamespaceId:
                branches = project.branches.list(retry_transient_errors=True)
                for branch in branches:
                    if branch.name == aBranch:
                        return True
                return False
        raise Exception("Project %s in %s not found" % (aProject, aNamespaceId))

    def project_exists(self, aNamespaceId, aProject):
        log.info('{0:30} {1}'.format('get_project', aProject))
        projects = self.gl.projects.list(search=aProject, retry_transient_errors=True)
        for project in projects:
            if project.name == aProject and project.namespace['id'] == aNamespaceId:
                return True
        return False

    def get_project_by_id(self, aProjectId):
        log.info('{0:30} {1}'.format('get_project_by_id', aProjectId))
        return self.gl.projects.get(aProjectId)

    def transfer(self, aProjectId, toNamespace):
        log.info('{0:30} move project:{1} to {2}'.format('transfer', aProjectId, toNamespace))
        grp = self.gl.groups.get(toNamespace)
        grp.transfer_project(aProjectId)

    def get_project(self, aNamespaceId, aProject):
        log.info('{0:30} {1}'.format('get_project', aProject))
        projects = self.gl.projects.list(search=aProject, retry_transient_errors=True)
        for project in projects:
            if project.name == aProject and project.namespace['id'] == aNamespaceId:
                return project
        raise Exception("Project %s not found (ns=%s)" % (aProject, aNamespaceId))

    def protect_branch(self, aProjectId, branch):
        log.info('{0:30} branch:{1} for project:{2}'.format('protect_branch', branch, aProjectId))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)
        branch = project.branches.get(branch, retry_transient_errors=True)
        branch.protect(retry_transient_errors=True)

    def delete_branch(self, aProjectId, branch):
        log.info('{0:30} branch:{1} for project:{2}'.format('delete_branch', branch, aProjectId))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)
        branches = project.branches.list(retry_transient_errors=True)
        for br in branches:
            if br.name == branch:
                log.info('{0:30} DELETE {1} for project:{2}'.format('', branch, aProjectId))
                br.delete(retry_transient_errors=True)

    def unprotect_branch(self, aProjectId, branch):
        log.info('{0:30} branch:{1} for project:{2}'.format('unprotect_branch', branch, aProjectId))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)
        branch = project.branches.get(branch, retry_transient_errors=True)
        branch.unprotect(retry_transient_errors=True)

    def share_project(self, aProjectId, aGroupId, access):
        log.info('{0:30} Access project:{1} by group:{2} with access:{3}'.format('share_project', aProjectId, aGroupId, access))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)
        try:
            for s in project.shared_with_groups:
                if (s['group_id'] == aGroupId and s['group_access_level'] != access):
                    log.info('{0:30} Access project:{1} by group:{2} - doing unshare then share.'.format('share_project', aProjectId, aGroupId))

                    project.unshare(aGroupId, retry_transient_errors=True)
                
            project.share(aGroupId, access, retry_transient_errors=True)
        except gitlab.exceptions.GitlabCreateError as error:
            if error.response_code == 409:
                return
            else:
                raise error

    def unshare_project(self, aProjectId, aGroupId):
        log.info('{0:30} Unshare project:{1} by group:{2}'.format('unshare_project', aProjectId, aGroupId))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)
        for s in project.shared_with_groups:
            if (s['group_id'] == aGroupId):
                project.unshare(aGroupId, retry_transient_errors=True)

    def get_project_shares(self, aProjectId):
        log.info('{0:30} Get project shares for:{1}'.format('get_project_shares', aProjectId))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)
        try:
            return project.shared_with_groups
        except gitlab.exceptions.GitlabCreateError as error:
            raise error

    def archive_project(self, aProjectId):
        log.info('{0:30} Archive project:{1}'.format('archive_project', aProjectId))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)

        archive_id = self.create_get_group("archive")
        project.name = "%s-%06d" % (project.name, project.id)
        project.path = "%s-%06d" % (project.name, project.id)
        project.save(retry_transient_errors=True)
        project.transfer_project (archive_id, retry_transient_errors=True)

        for s in project.shared_with_groups:
            project.unshare(s['group_id'], retry_transient_errors=True)

    def create_get_fork(self, aProjectId, aGroupName):
        log.info('{0:30} Create fork of project:{1} to group:{2}'.format('create_get_fork', aProjectId, aGroupName))

        project = self.gl.projects.get(aProjectId)

        forks = project.forks.list()
        for fork in forks:
            if fork.namespace['name'] == aGroupName:
                return fork.id

        log.info('{0:30} {1} CREATING'.format('', aGroupName))
        fork = project.forks.create({'namespace': aGroupName})
        return fork.id

    def create_hook(self, url, token = None):
        log.info('{0:30} {1}'.format('create_hook', url))
        hooks = self.gl.hooks.list()
        for hook in hooks:
            if hook.url == url:
                return
        log.info('{0:30} {1} CREATED'.format('', url))
        hook = self.gl.hooks.create({'url': url, 'token': token, 'enable_ssl_verification': False, 'merge_requests_events': True, 'repository_update_events': True})

    def add_deploy_key (self, aProjectId, key_name, pub_key):
        log.info('{0:30} Add deploy key:{1} {2}'.format('add_deploy_key', aProjectId, key_name))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)
        for k in project.keys.list():
            if k.title == key_name:
                log.info('{0:30} Add deploy key:{1} {2} ALREADY CREATED.'.format('add_deploy_key', aProjectId, key_name))
                return

        key = project.keys.create({'title': key_name,
                           'key': pub_key})
        log.info('{0:30} Add deploy key:{1} {2} CREATED.'.format('add_deploy_key', aProjectId, key_name))

    def add_file (self, aProjectId, branch, fileName, fileContents, message = None):
        log.info('{0:30} Add file:{1} in branch {2} file:{3}'.format('add_file', aProjectId, branch, fileName))
        project = self.gl.projects.get(aProjectId, retry_transient_errors=True)
        try:
            f = project.files.get(file_path=fileName, ref=branch, retry_transient_errors=True)
            f.content = fileContents
            f.save(branch=branch, commit_message="Update %s" % fileName, retry_transient_errors=True)

        except gitlab.exceptions.GitlabGetError as error:
            if error.response_code == 404:
                f = project.files.create({'file_path': fileName,
                                'branch': branch,
                                'content': fileContents,
                                'author_email': 'no-reply@popdata.local',
                                'author_name': 'Automation Agent',
                                'commit_message': "Added %s" % fileName if (message is None) else message}, retry_transient_errors=True)
                log.info(f)

