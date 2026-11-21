"""Unit tests for SCM provider discovery and credential sanitization."""

import pytest
from pr_review.models.base import SCMProviderType
from pr_review.scm.discovery import SCMDiscovery, sanitize_url


def test_sanitize_url_removes_tokens_and_passwords():
    raw_url = "https://x-access-token:ghp_SecretToken123@github.com/myorg/myrepo.git"
    clean = sanitize_url(raw_url)
    assert "ghp_SecretToken123" not in clean
    assert "://***:***@github.com" in clean


def test_detect_github_multi_signal():
    discovery = SCMDiscovery()
    env = {
        "GIT_URL": "https://github.com/acme/project.git",
        "CHANGE_ID": "42",
        "CHANGE_TARGET": "main",
    }
    provider, score = discovery.discover(env)
    assert provider.provider_type == SCMProviderType.GITHUB
    assert score >= 0.5


def test_detect_gitlab_signals():
    discovery = SCMDiscovery()
    env = {
        "GITLAB_CI": "true",
        "CI_MERGE_REQUEST_IID": "15",
        "GIT_URL": "https://gitlab.com/group/repo.git",
    }
    provider, score = discovery.discover(env)
    assert provider.provider_type == SCMProviderType.GITLAB


def test_detect_bitbucket_signals():
    discovery = SCMDiscovery()
    env = {
        "BITBUCKET_BUILD_NUMBER": "100",
        "GIT_URL": "https://bitbucket.org/team/repo.git",
    }
    provider, score = discovery.discover(env)
    assert provider.provider_type == SCMProviderType.BITBUCKET


def test_detect_azure_repos():
    discovery = SCMDiscovery()
    env = {
        "TF_BUILD": "True",
        "GIT_URL": "https://dev.azure.com/organization/project/_git/repo",
    }
    provider, score = discovery.discover(env)
    assert provider.provider_type == SCMProviderType.AZURE_DEVOPS


def test_inconclusive_detection_falls_back_to_generic():
    discovery = SCMDiscovery()
    env = {
        "GIT_COMMIT": "abc1234",
    }
    provider, score = discovery.discover(env)
    # Should fall back cleanly without failing or claiming remote blocking
    assert provider.provider_type == SCMProviderType.GENERIC_GIT
    assert provider.post_status(None, None) is False  # PR publishing marked unavailable
