from datetime import datetime

from openra.services.github import GithubRelease, GithubReleaseAsset


class FakeGithub():

    only_one_release = False
    only_ra_asset = False

    def get_releases(self):
        if self.only_one_release:
            return [
                GithubRelease('release-5', datetime.now()),
            ]

        return [
            GithubRelease('playtest-7', datetime.now()),
            GithubRelease('playtest-6', datetime.now()),
            GithubRelease('release-5', datetime.now()),
            GithubRelease('playtest-4', datetime.now()),
            GithubRelease('release-3', datetime.now()),
            GithubRelease('playtest-2', datetime.now()),
            GithubRelease('release-1', datetime.now())
        ]

    def get_release_assets(self, tag):
        if self.only_ra_asset:
            return [
                GithubReleaseAsset('OpenRA-Red-Alert-version.AppImage', 'sample_ra_url'),
            ]

        return [
            GithubReleaseAsset('OpenRA-Red-Alert-version.exe', 'sample_ra_exe_url'),
            GithubReleaseAsset('OpenRA-Red-Alert-version.AppImage', 'sample_ra_url'),
            GithubReleaseAsset('OpenRA-Tiberian-Dawn-version.AppImage', 'sample_td_url'),
            GithubReleaseAsset('OpenRA-Dune-2000-version.AppImage', 'sample_d2k_url'),
        ]
