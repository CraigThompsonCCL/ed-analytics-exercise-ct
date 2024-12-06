from pydantic import BaseModel


class GitHubPR(BaseModel):
    url: str
    id: int

    def __eq__(self, other):
        if isinstance(other, GitHubPR):
            return self.id == other.id
        return False
