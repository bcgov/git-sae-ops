
import gitlab

class ProjectOp():
    def __init__(self, glapi):
        self.glapi = glapi

    def run (self, saeProjectName):
        glapi = self.glapi

        glapi.create_get_group(saeProjectName)

    def create_group (self, saeProjectName):
        glapi = self.glapi

        glapi.create_get_group(saeProjectName)

    def get_group (self, saeProjectName):
        glapi = self.glapi

        return glapi.get_group(saeProjectName)

    def get_all_groups (self):
        glapi = self.glapi

        return glapi.get_all_groups()

    def get_project_by_id (self, repo):
        glapi = self.glapi

        return glapi.get_project_by_id(repo)

    def transfer (self, project_id, namespace):
        glapi = self.glapi

        return glapi.transfer(project_id, namespace)


