from fastapi import APIRouter
from fastapi_cache.decorator import cache
from ..models.github import GitHubPR
from . import async_client
import httpx

router = APIRouter(prefix="/github", tags=["github"])

newest_pr: GitHubPR | None = None
total_pr_count: int = 0
lodash_prs_list: list[GitHubPR] = []
lodash_prs_dict: dict[int, GitHubPR] = {}


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
    global newest_pr
    global total_pr_count
    former_newest_pr = newest_pr
    newest_pr_replaced = False

    # Quick version - under conservative assumptions, will be called >99% of the time
    new_pr_count = 0
    former_newest_pr_found = False
    if newest_pr:
        response = await async_client.get(
            "https://api.github.com/repos/lodash/lodash/pulls?per_page=5&state=all"
        )
        for raw_pr in response.json():
            pr = GitHubPR.model_validate(raw_pr)
            # replace newest PR in database
            if not newest_pr_replaced:
                newest_pr_replaced = True
                newest_pr = pr
            if pr == former_newest_pr:
                former_newest_pr_found = True
                break
            else:
                new_pr_count += 1
                lodash_prs_list.append(pr)
                lodash_prs_dict[pr.id] = pr
        if former_newest_pr_found:
            total_pr_count += new_pr_count
            return total_pr_count

    # Will likely only be called <1% of the time, including application startup
    new_pr_count = 0
    former_newest_pr_found = False
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
                new_pr_count += 1
                lodash_prs_list.append(pr)
                lodash_prs_dict[pr.id] = pr
        if not former_newest_pr_found:
            next_page_url = get_link(response, "next")
    total_pr_count += new_pr_count
    return total_pr_count


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
