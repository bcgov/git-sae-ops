import os
import gitlab
import logging

class RepoOp():
    def __init__(self, glapi):
        self.glapi = glapi

    def join (self, saeProjectName, repoName):
        glapi = self.glapi

        shareGroup = glapi.get_group('shares')

        teamGroup = glapi.get_group(saeProjectName)
        glrepo = glapi.get_project(shareGroup.id, repoName)
        
        self.validate_private_repo (glrepo, saeProjectName)

        glapi.share_project(glrepo.id, teamGroup.id, gitlab.DEVELOPER_ACCESS)

    def leave (self, saeProjectName, repoName):
        glapi = self.glapi

        shareGroup = glapi.get_group('shares')
        teamGroup = glapi.get_group(saeProjectName)
        glrepo = glapi.get_project(shareGroup.id, repoName)
        
        glapi.unshare_project(glrepo.id, teamGroup.id)

    def repair (self, saeProjectName, repoName):
        log = logging.getLogger(__name__)

        glapi = self.glapi

        tries = 1
        failed = True
        while (failed == True and tries < 3):
            log.debug("REPAIR %20s (Attempt %d)" % (repoName, tries))
            try:
                public = glapi.create_get_group("ocwa-checkpoint")
                publicRepo = glapi.create_get_project(public, repoName)

                glapi.create_get_branch(public, repoName, "private")
                glapi.set_default_branch(public, repoName, "private")
                glapi.protect_branch(publicRepo, "private")
                glapi.protect_branch(publicRepo, "master")

                sharedGroup = glapi.create_get_group("shares")
                glrepo = glapi.create_get_project(sharedGroup, repoName)

                glapi.create_get_branch(sharedGroup, repoName, "develop")
                glapi.set_default_branch(sharedGroup, repoName, "develop")
                glapi.unprotect_branch(glrepo, "develop")
                #glapi.delete_branch(glrepo, "master")

                glapi.add_file(glrepo, 'develop', 'LICENSE', open("%s/%s" % (os.path.dirname(os.path.abspath(__file__)), "assets/LICENSE"),"r").read())
                glapi.add_file(glrepo, 'develop', 'README.md', open("%s/%s" % (os.path.dirname(os.path.abspath(__file__)), "assets/README.md"),"r").read())
                glapi.add_file(glrepo, 'develop', 'CONTRIBUTING.md', open("%s/%s" % (os.path.dirname(os.path.abspath(__file__)), "assets/CONTRIBUTING.md"),"r").read())
                glapi.add_file(glrepo, 'develop', 'CODE_OF_CONDUCT.md', open("%s/%s" % (os.path.dirname(os.path.abspath(__file__)), "assets/CODE_OF_CONDUCT.md"),"r").read())

                failed = False
            except KeyboardInterrupt:
                raise
            except:
                log.error("REPAIR ERROR %20s (Attempt %d)" % (repoName, tries))
                log.error("Unexpected error:", sys.exc_info()[0])
                tries = tries + 1

        if failed == True:
            raise Exception("Failed to repair project")

    def run (self, saeProjectName, repoName, private):
        glapi = self.glapi

        # Get the outputchecker group
        ocGroup = glapi.create_get_group("oc")

        # Have a 'checkpoint' group that controls movement of files in/out of the SRE
        public = glapi.create_get_group("ocwa-checkpoint")

        if glapi.project_exists(public, repoName):
            raise Exception("Project %s already exists" % repoName)

        publicRepo = glapi.create_get_project(public, repoName)
        glapi.config_project_variant2(publicRepo)
        glapi.share_project(publicRepo, ocGroup, gitlab.DEVELOPER_ACCESS)

        # Create the corresponding internal group
        sharedGroup = glapi.create_get_group("shares")
        teamGroup = glapi.create_get_group("%s" % saeProjectName)
        glrepo = glapi.create_get_project(sharedGroup, repoName)
        
        if private:
            self.do_private_repo_validation(glrepo, saeProjectName)
            glapi.config_project_variant_private(glrepo)
        else:
            glapi.config_project_variant_shared(glrepo)

        glapi.share_project(glrepo, ocGroup, gitlab.REPORTER_ACCESS)
        glapi.share_project(glrepo, teamGroup, gitlab.DEVELOPER_ACCESS)

        try:
            glapi.create_get_branch(public, repoName, "private")
            glapi.set_default_branch(public, repoName, "private")
            glapi.protect_branch(publicRepo, "private")
            glapi.protect_branch(publicRepo, "master")

            glapi.create_get_branch(sharedGroup, repoName, "develop")
            glapi.set_default_branch(sharedGroup, repoName, "develop")
            glapi.unprotect_branch(glrepo, "develop")
            glapi.delete_branch(glrepo, "master")

            glapi.add_file(glrepo, 'develop', 'LICENSE', open("%s/%s" % (os.path.dirname(os.path.abspath(__file__)), "assets/LICENSE"),"r").read())
            glapi.add_file(glrepo, 'develop', 'README.md', open("%s/%s" % (os.path.dirname(os.path.abspath(__file__)), "assets/README.md"),"r").read())
            glapi.add_file(glrepo, 'develop', 'CONTRIBUTING.md', open("%s/%s" % (os.path.dirname(os.path.abspath(__file__)), "assets/CONTRIBUTING.md"),"r").read())
            glapi.add_file(glrepo, 'develop', 'CODE_OF_CONDUCT.md', open("%s/%s" % (os.path.dirname(os.path.abspath(__file__)), "assets/CODE_OF_CONDUCT.md"),"r").read())
        except:
            self.repair(saeProjectName, repoName)


    def do_private_repo_validation (self, glrepo, project_name):
        glapi = self.glapi

        nonMaintainerGroups = 0

        shares = glapi.get_project_shares(glrepo)

        for s in shares:
            if (s['group_access_level'] == 30 and s['group_name'] != project_name):
                nonMaintainerGroups = nonMaintainerGroups + 1
        
        if (nonMaintainerGroups > 0):
            raise Exception("Private repos can only have one Developer group associated.")

    def validate_private_repo (self, project, project_name):
        shares = project.shared_with_groups

        nonMaintainerGroups = 0

        if project.issues_enabled == False:
            return

        for s in shares:
            if (s['group_access_level'] == 30 and s['group_name'] != project_name):
                nonMaintainerGroups = nonMaintainerGroups + 1
        
        if (nonMaintainerGroups > 0):
            raise Exception("Private repos can only have one Developer group associated.")

