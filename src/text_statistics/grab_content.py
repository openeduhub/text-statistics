from typing import Optional
import trafilatura
from trafilatura.settings import use_config


def grab_content(
    url: str,
    target_language: Optional[str] = None,
    favor_recall=False,
    favor_precision=False,
) -> Optional[str]:
    # disable signal, because it causes issues with the web-service
    newconfig = use_config()
    newconfig.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")

    downloaded = trafilatura.fetch_url(url, config=newconfig)

    if downloaded is None:
        return None

    result = trafilatura.extract(
        downloaded,
        url=url,
        favor_recall=favor_recall,
        favor_precision=favor_precision,
        target_language=target_language,
        config=newconfig,
    )
    return result


def main():
    pass


if __name__ == "__main__":
    main()
