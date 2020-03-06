import os
from clients.git_api import GitAPI
from clients.file_api import FileUtils
from clients.gitlab_api import GitlabAPI
from dirsync import sync

class PushChanges():
    def __init__(self, config):
        self.projectsc_host = config['projectsc']['host']
        self.projectsc_token = config['projectsc']['token']
        self.github_token = config['github']['token']
        self.git_user = config['git_user']

    def push_to_external (self, repoName, importUrl, branch):
        glapi = GitlabAPI(self.projectsc_host, self.projectsc_token)

        checkpoint = glapi.create_get_group("ocwa-checkpoint")

        cpRepo = glapi.get_project(checkpoint, repoName)

        if glapi.has_branch (checkpoint, repoName, branch) == False:
            raise Exception("Push to external rejected.  Branch '%s' not found." % branch)

        if importUrl is None:
            importUrl = glapi.get_custom_attribute(cpRepo.id, 'external_url')

        # Source
        publicRepoUrl = glapi.get_project(checkpoint, repoName).http_url_to_repo
        sgit = GitAPI(publicRepoUrl, self.projectsc_token)
        commitRef = sgit.checkout("%s" % branch)
        sgit.info()

        # Target
        tgit = GitAPI(importUrl, self.github_token)
        tgit.info()
        if tgit.is_empty():
            tgit.init_repo()

        if tgit.has_branch(branch):
            tgit.checkout(branch)
        else:
            tgit.checkout_new(branch)
        tgit.set_user(self.git_user['username'], self.git_user['email'])

        # Don't ever copy the .gitlab-ci.yml file!
        os.remove ("%s/.gitlab-ci.yml" % sgit.dir())

        # Do a full copy from source to target
        fileutils = FileUtils()
        fileutils.copytree (sgit.dir(), tgit.dir())
        fileutils.sync_deletions (sgit.dir(), tgit.dir())

        if len(tgit.has_changes()) > 0:
            # Commit the changes to the target repo
            tgit.commit_and_push(branch, "Changes (%s) from SAE environment" % commitRef.hexsha[0:7])
        else: 
            print("-- No changes so no commit and push performed")

        glapi.delete_branch(cpRepo.id, "%s-outgoing" % branch)

    def push_to_sae (self, repoName, branch):
        glapi = GitlabAPI(self.projectsc_host, self.projectsc_token)

        # Source
        public = glapi.create_get_group("ocwa-checkpoint")
        publicRepoUrl = glapi.get_project(public, repoName).http_url_to_repo
        sgit = GitAPI(publicRepoUrl, self.projectsc_token)
        commitRef = sgit.checkout("%s" % branch)
        sgit.info()

        # Target
        shares = glapi.create_get_group("shares")
        sreRepoUrl = glapi.get_project(shares, repoName).http_url_to_repo
        tgit = GitAPI(sreRepoUrl, self.projectsc_token)
        tgit.info()
        if tgit.has_branch(branch):
            tgit.checkout(branch)
        else:
            tgit.checkout_new(branch)
        tgit.set_user(self.git_user['username'], self.git_user['email'])

        # Don't ever copy the .gitlab-ci.yml file!
        os.remove ("%s/.gitlab-ci.yml" % sgit.dir())

        # Do a full copy from source to target
        fileutils = FileUtils()
        fileutils.copytree (sgit.dir(), tgit.dir())
        fileutils.sync_deletions (sgit.dir(), tgit.dir())

        if len(tgit.has_changes()) > 0:
            # Commit the changes to the target repo
            tgit.commit_and_push(branch, "Changes (%s) to SAE environment" % commitRef.hexsha[0:7])
        else: 
            print("-- No changes so no commit and push performed")
        
        glapi.delete_branch(glapi.get_project(public, repoName).id, "%s-incoming" % branch)
