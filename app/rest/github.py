from fastapi import APIRouter
from fastapi_cache.decorator import cache
from ..models.github import GitHubPR
from . import async_client
import httpx

router = APIRouter(prefix="/github", tags=["github"])

lodash_prs_list: list[GitHubPR] = []


@router.get("/quick_lodash_pr_count")
@cache(expire=60)
async def get_lodash_prs_quick() -> int:
    """
    A fast implementation to get the count of all lodash PRs.
    Makes an unassured (but very likey) assumption about how GitHub will page this API.
    """
    response = await async_client.get(
        "https://api.github.com/repos/lodash/lodash/pulls?per_page=1&state=all"
    )
    link_text = get_link(response, "last")
    return int(link_text.split("=")[-1])


# @app.get("/perf_get_prs")
# def get_5_prs() -> tuple[float, float, float]:
#     start = time.perf_counter()
#     async_client.get(
#         "https://api.github.com/repos/lodash/lodash/pulls?per_page=100&state=all"
#     )
#     hundred = time.perf_counter()
#     async_client.get("https://api.github.com/repos/lodash/lodash/pulls?per_page=5&state=all")
#     five = time.perf_counter()
#     async_client.get("https://api.github.com/repos/lodash/lodash/pulls?per_page=2&state=all")
#     two = time.perf_counter()
#     return hundred - start, five - hundred, two - five


@router.get("/lodash_pr_count")
@cache(expire=60)
async def get_lodash_prs() -> int:
    """Get the count of all lodash PRs."""
    global lodash_prs_list
    prs_list_copy = lodash_prs_list[:]
    former_newest_pr = prs_list_copy[0] if len(prs_list_copy) else None

    # Quick version - under conservative assumptions, will be called >99% of the time
    former_newest_pr_found = False
    new_prs_list = []
    if former_newest_pr:
        response = await async_client.get(
            "https://api.github.com/repos/lodash/lodash/pulls?per_page=5&state=all"
        )
        for raw_pr in response.json():
            pr = GitHubPR.model_validate(raw_pr)
            if pr == former_newest_pr:
                former_newest_pr_found = True
                break
            else:
                new_prs_list.append(pr)
        if former_newest_pr_found:
            # store data
            lodash_prs_list = new_prs_list + prs_list_copy
            return len(prs_list_copy) + len(new_prs_list)

    # Will likely only be called <1% of the time, including application startup
    former_newest_pr_found = False
    new_prs_list = []
    next_page_url = (
        "https://api.github.com/repos/lodash/lodash/pulls?per_page=100&state=all"
    )
    while next_page_url and not former_newest_pr_found:
        response = await async_client.get(next_page_url)
        for raw_pr in response.json():
            pr = GitHubPR.model_validate(raw_pr)
            if pr == former_newest_pr:
                former_newest_pr_found = True
                break
            else:
                new_prs_list.append(pr)
        if not former_newest_pr_found:
            next_page_url = get_link(response, "next")
    # store data
    lodash_prs_list = new_prs_list + prs_list_copy
    return len(prs_list_copy) + len(new_prs_list)


def get_link(response: httpx.Response, link_type: str) -> str | None:
    link_header = response.headers.get("link", {})
    links = link_header.split(",")
    next_link = None
    for link in links:
        rel = link[-5:-1]
        if rel == link_type:
            next_link = link.split(">")[0].strip()[1:]
            break
    return next_link
