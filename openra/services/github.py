from github import Github as GithubClient
from openra import settings

class Github():

    def listReleases(self):
        repo = self._getRepo()
#
        releases = repo.get_releases()

        output = []

        for release in releases:
            output.append({
                "tag":release.tag_name,
                "published":release.published_at,
            })

        return output

    def getReleaseAssets(self, tag):
        repo = self._getRepo()
#
        release = repo.get_release(tag)

        assets = release.get_assets()
        output = []

        for asset in assets:
            output.append({
                "name":asset.name,
                "url":asset.browser_download_url,
            })

        return output

    def _getClient(self):
        return GithubClient(settings.GITHUB_API_KEY)

    def _getRepo(self):
        github = self._getClient()

        return github.get_repo(settings.GITHUB_OPENRA_REPO, lazy=True)

