from services.draft_workflow import run_draft
from services.wechat_client import DraftCreationResultUnknown, WeChatApiError
from utils.google_sheets import prompt_draft_period
import time


def show_progress(message):
    print(message, flush=True)


def main():
    start = time.time()
    digest = input("Digest: ")
    try:
        period = prompt_draft_period()
        result = run_draft(period, digest, progress=show_progress)
    except ValueError as error:
        print(error)
        return
    except WeChatApiError as error:
        print(error.response)
        return
    except DraftCreationResultUnknown as error:
        print(error)
        return

    print(f"Completed in {time.time() - start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
