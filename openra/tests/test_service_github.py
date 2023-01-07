import datetime

from unittest import TestCase
from unittest.mock import  Mock, MagicMock
from django.conf import settings
from openra.services.github import ErrorGithubReleaseAssetsException, ErrorGithubReleaseException, Github, GithubRelease, GithubReleaseAsset

class TestServiceGithub(TestCase):

    def test_will_obtain_release_data_from_github(self):
        published_date = datetime.datetime

        repo_mock = Mock()
        repo_mock.get_releases = MagicMock(
            return_value = [
                Mock(tag_name="sample1", published_at=published_date),
                Mock(tag_name="sample2", published_at=published_date)
            ]
        )

        client_mock = Mock()
        client_mock.get_repo = MagicMock(
            return_value = repo_mock
        )

        github = Github(client_mock)

        releases = github.get_releases().unwrap()

        self.assertIsInstance(
            releases[0],
            GithubRelease
        )

        self.assertEquals(
            'sample1',
            releases[0].tag
        )

        self.assertEquals(
            'sample2',
            releases[1].tag
        )

        self.assertEquals(
            published_date,
            releases[0].published
        )

        self.assertEquals(
            published_date,
            releases[1].published
        )

        repo_mock.get_releases.assert_called_once_with()

        client_mock.get_repo.assert_called_once_with(
            settings.GITHUB_OPENRA_REPO,
            lazy=True
        )

    def test_will_return_err_for_get_releases_exceptions(self):
        client_mock = Mock()
        client_mock.get_repo = MagicMock(
            side_effect = Exception()
        )

        github = Github(client_mock)

        err = github.get_releases()

        self.assertTrue(
            err.is_err()
        )

        self.assertIsInstance(
            err.unwrap_err(),
            ErrorGithubReleaseException
        )

    def test_will_return_assets_for_a_release(self):
        release_mock = Mock()

        mock_asset1 = Mock(browser_download_url="url1")
        mock_asset1.configure_mock(name="asset1")
        mock_asset2 = Mock(browser_download_url="url2")
        mock_asset2.configure_mock(name="asset2")

        release_mock.get_assets = MagicMock(
            return_value = [
                mock_asset1,
                mock_asset2,
            ]
        )

        repo_mock = Mock()
        repo_mock.get_release = MagicMock(
            return_value = release_mock
        )

        client_mock = Mock()
        client_mock.get_repo = MagicMock(
            return_value = repo_mock
        )

        github = Github(client_mock)

        assets = github.get_release_assets('release_tag').unwrap()

        self.assertIsInstance(
            assets[0],
            GithubReleaseAsset
        )

        self.assertEquals(
            'url1',
            assets[0].url
        )

        self.assertEquals(
            'url2',
            assets[1].url
        )

        self.assertEquals(
            'asset1',
            assets[0].name
        )

        self.assertEquals(
            'asset2',
            assets[1].name
        )

        release_mock.get_assets.assert_called_once_with()

        repo_mock.get_release.assert_called_once_with(
            'release_tag'
        )

        client_mock.get_repo.assert_called_once_with(
            settings.GITHUB_OPENRA_REPO,
            lazy=True
        )

    def test_will_return_err_for_get_release_assets_exceptions(self):
        client_mock = Mock()
        client_mock.get_repo = MagicMock(
            side_effect = Exception()
        )

        github = Github(client_mock)

        err = github.get_release_assets('123')

        self.assertTrue(
            err.is_err()
        )

        self.assertIsInstance(
            err.unwrap_err(),
            ErrorGithubReleaseAssetsException
        )

    def test_will_only_get_the_repo_once_over_multiple_calls(self):
        release_mock = Mock()
        release_mock.get_assets = MagicMock(
            return_value = []
        )
        repo_mock = Mock()
        repo_mock.get_releases = MagicMock(
            return_value = []
        )
        repo_mock.get_release = MagicMock(
            return_value = release_mock
        )
        client_mock = Mock()
        client_mock.get_repo = MagicMock(
            return_value = repo_mock
        )

        github = Github(client_mock)

        github.get_releases()
        github.get_release_assets('sample')

        client_mock.get_repo.assert_called_once()
        repo_mock.get_releases.assert_called_once()
        repo_mock.get_release.assert_called_once()
        release_mock.get_assets.assert_called_once()
