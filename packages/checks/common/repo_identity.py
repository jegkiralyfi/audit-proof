from __future__ import annotations

from typing import Any
from urllib.parse import quote, urlparse


def _github_parts(url: str) -> tuple[str | None, str | None]:
    path = urlparse(url).path.strip('/')
    parts = [p for p in path.split('/') if p]
    if len(parts) < 2:
        return None, None
    owner, repo = parts[0], parts[1]
    if repo.endswith('.git'):
        repo = repo[:-4]
    return owner, repo


def _gitlab_parts(url: str) -> tuple[str | None, str | None]:
    path = urlparse(url).path.strip('/')
    parts = [p for p in path.split('/') if p]
    if len(parts) < 2:
        return None, None
    owner = '/'.join(parts[:-1])
    repo = parts[-1]
    if repo.endswith('.git'):
        repo = repo[:-4]
    return owner, repo


def normalize_repository_identity(url: str | None, provider: str | None) -> dict[str, Any]:
    if not url:
        return {}
    provider = (provider or '').lower().strip()
    if provider == 'github':
        owner, repo = _github_parts(url)
        if owner and repo:
            return {
                'normalized_owner': owner,
                'normalized_repo': repo,
                'normalized_full_name': f'{owner}/{repo}',
                'repository_identity': f'github:{owner}/{repo}',
                'api_url': f'https://api.github.com/repos/{owner}/{repo}',
            }
    if provider == 'gitlab':
        owner, repo = _gitlab_parts(url)
        if owner and repo:
            full = f'{owner}/{repo}'
            return {
                'normalized_owner': owner,
                'normalized_repo': repo,
                'normalized_full_name': full,
                'repository_identity': f'gitlab:{full}',
                'api_url': f'https://gitlab.com/api/v4/projects/{quote(full, safe="")}',
            }
    host = urlparse(url).netloc.lower() or (provider or 'unknown')
    path = urlparse(url).path.strip('/')
    identity = f'{host}:{path}' if path else host
    return {
        'repository_identity': identity,
    }
