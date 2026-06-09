from services.draft_workflow import run_draft
from services.wechat_client import DraftCreationResultUnknown, WeChatApiError
from utils.google_sheets import prompt_draft_period
import time


def main():
    start = time.time()
    digest = input("digest: ")
    try:
        period = prompt_draft_period()
        result = run_draft(period, digest)
    except ValueError as error:
        print(error)
        return
    except WeChatApiError as error:
        print(error.response)
        return
    except DraftCreationResultUnknown as error:
        print(error)
        return

    print(result.media_id)
    print(time.time() - start)


if __name__ == "__main__":
    main()
