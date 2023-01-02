import datetime

from unittest import TestCase
from unittest.mock import  Mock, MagicMock
from django.conf import settings
from openra.services.github import Github

class TestServiceGithub(TestCase):

    def test_will_obtain_release_data_from_github(self):
        publishedDate = datetime.datetime

        repoMock = Mock()
        repoMock.get_releases = MagicMock(
            return_value = [
                Mock(tag_name="sample1", published_at=publishedDate),
                Mock(tag_name="sample2", published_at=publishedDate)
            ]
        )

        clientMock = Mock()
        clientMock.get_repo = MagicMock(
            return_value = repoMock
        )

        github = Github()

        github._getClient = MagicMock(
            return_value = clientMock
        )

        self.assertEquals([{
                "tag":"sample1",
                "published":publishedDate,
            },{
                "tag":"sample2",
                "published":publishedDate,
            }],
            github.listReleases()
        )

        repoMock.get_releases.assert_called_once_with()

        clientMock.get_repo.assert_called_once_with(
            settings.GITHUB_OPENRA_REPO,
            lazy=True
        )

    def test_will_return_assets_for_a_release(self):
        releaseMock = Mock()

        mockAsset1 = Mock(browser_download_url="url1")
        mockAsset1.configure_mock(name="asset1")
        mockAsset2 = Mock(browser_download_url="url2")
        mockAsset2.configure_mock(name="asset2")

        releaseMock.get_assets = MagicMock(
            return_value = [
                mockAsset1,
                mockAsset2,
            ]
        )

        repoMock = Mock()
        repoMock.get_release = MagicMock(
            return_value = releaseMock
        )

        clientMock = Mock()
        clientMock.get_repo = MagicMock(
            return_value = repoMock
        )

        github = Github()

        github._getClient = MagicMock(
            return_value = clientMock
        )

        self.assertEquals([{
                "name":"asset1",
                "url":"url1",
            },{
                "name":"asset2",
                "url":"url2",
            }],
            github.getReleaseAssets('release_tag')
        )

        releaseMock.get_assets.assert_called_once_with()

        repoMock.get_release.assert_called_once_with(
            'release_tag'
        )

        clientMock.get_repo.assert_called_once_with(
            settings.GITHUB_OPENRA_REPO,
            lazy=True
        )
