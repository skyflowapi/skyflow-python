from urllib.parse import urlparse

def get_base_url(url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

def format_scope(scopes):
    if not scopes:
        return None
    return " ".join([f"role:{scope}" for scope in scopes])