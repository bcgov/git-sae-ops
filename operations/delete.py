
from clients.gitlab_api import GitlabAPI

class Delete():
    def __init__(self, config):
        self.projectsc_host = config['projectsc']['host']
        self.projectsc_token = config['projectsc']['token']
        self.github_token = config['github']['token']
        self.git_user = config['git_user']

    def delete (self, project_name):
        glapi = GitlabAPI(self.projectsc_host, self.projectsc_token)

        namespace = glapi.get_group("shares")
        project_shares = glapi.get_project(namespace.id, project_name)
        glapi.archive_project(project_shares.id)

        namespace = glapi.get_group("ocwa-checkpoint")
        project_checkpoint = glapi.get_project(namespace.id, project_name)
        glapi.archive_project(project_checkpoint.id)
