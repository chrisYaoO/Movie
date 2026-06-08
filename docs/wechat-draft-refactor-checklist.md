# WeChat Draft Refactor Checklist

## Objective

Refactor the WeChat Official Account draft workflow while preserving the
behavior of the stable baseline:

- Stable branch: `main`
- Stable tag: `wechat-draft-baseline-2026-06-08`
- Refactor branch: `refactor/wechat-draft`

The workflow currently reads movie records from Google Sheets, uploads poster
images to WeChat, renders article HTML, and creates one WeChat draft.

## Safety Rules

- [x] Preserve the stable version on `main` and the baseline tag.
- [x] Work only on `refactor/wechat-draft`.
- [x] Establish characterization tests before changing workflow behavior.
- [x] Keep every refactor stage independently reviewable and revertible.
- [x] Run `python -m unittest discover -v` before every refactor commit.
- [x] Do not call real Google Sheets, Douban, or WeChat APIs from automated tests.
- [x] Do not add a final confirmation gate to a Draft Run.

## Decisions To Resolve

- [x] Keep preview generation and draft publication in one end-to-end Draft Run.
- [x] Draft Run inputs are period and Digest; author, thumbnail, source URL, and
      credentials come from `configs/ids.json`.
- [x] Preserve current empty Digest behavior: send a single space to WeChat.
- [x] If any poster upload fails, stop the Draft Run and do not create a draft.
- [x] Do not cache poster uploads; reruns upload posters again from the beginning.
- [x] Remove the local Google Sheets backup written during Draft Runs.
- [x] Store the Preview at `outputs/movie_wechat.html` and overwrite it on each Draft Run.
- [x] Do not introduce run manifests.
- [x] Invalid Draft Period input ends the Draft Run with a clear error; blank
      input may use current-year and current-month defaults.
- [x] A Draft Period with no movies ends the Draft Run before uploads or draft creation.
- [x] Any selected movie with missing required fields ends the Draft Run and
      reports its sheet row and missing fields.
- [x] Required Draft Movie fields are `date`, `name`, `director`, `year`,
      `rating`, `comment`, `movie_id`, and `image_id`; `comment` may be empty,
      and `quality` is not required.
- [x] A draft-creation timeout reports an unknown result, is not automatically
      retried, and reminds the user to check WeChat before rerunning.
- [x] Display WeChat API business-error responses directly.
- [x] Obtain one access token per Draft Run and reuse it without automatic refresh.
- [x] Preserve current same-year title rules; Draft Periods do not span years.
- [x] Preserve Google Sheets row order for Draft Movies.
- [x] Delete the unrelated Web App workflow only after the refactored Draft Run
      is verified, using a separate commit.

## Phase 1: WeChat Client

- [ ] Add characterization tests for access-token success and WeChat API errors.
- [ ] Introduce one WeChat client module for token retrieval, image upload, and
      draft creation.
- [ ] Reuse one access token across poster uploads and draft creation.
- [ ] Move WeChat endpoint construction and response validation behind the
      client interface.
- [ ] Move author, thumbnail media ID, and source URL out of hard-coded request
      construction and into `configs/ids.json`.
- [ ] Validate all required WeChat configuration before calling the WeChat API.
- [ ] Add consistent request timeouts.
- [ ] Distinguish definite WeChat API failures from unknown draft-creation timeout results.
- [ ] Preserve the full WeChat business-error response for display.
- [ ] Preserve the characterized draft request and return value.
- [ ] Run the full test suite and commit.

## Phase 2: Draft Movie Selection

- [ ] Add characterization tests for an empty month, missing headers, malformed
      dates, and missing required movie fields.
- [ ] Replace the current identity-based empty-list check with reliable empty-period validation.
- [ ] Separate interactive period input from Google Sheets reading.
- [ ] Introduce an explicit period value used by the draft workflow.
- [ ] Preserve blank-input defaults while rejecting invalid Draft Period input.
- [ ] Return validated draft movie records instead of loosely shaped dictionaries.
- [ ] Include sheet row numbers in Draft Movie validation errors.
- [ ] Preserve current title generation and title splitting unless a decision
      explicitly changes them.
- [ ] Preserve Google Sheets row order without sorting Draft Movies.
- [ ] Remove backup-writing behavior from Draft Runs.
- [ ] Run the full test suite and commit.

## Phase 3: Draft Workflow

- [ ] Add an end-to-end offline test covering selection, poster upload, rendering,
      and draft creation through fake external adapters.
- [ ] Introduce one workflow entry point that coordinates a complete draft run.
- [ ] Make `wechat.py` responsible only for command input, workflow invocation,
      and result display.
- [ ] Preserve current empty Digest behavior behind a named rule.
- [ ] Remove wildcard imports from the draft path.
- [ ] Return a structured run result containing title, movie count, preview path,
      and WeChat draft media ID.
- [ ] Run the full test suite and commit.

## Phase 4: Recovery And Outputs

- [ ] Stop before draft creation when any poster upload fails.
- [ ] Store the Preview at `outputs/movie_wechat.html`.
- [ ] Warn the user to inspect WeChat before rerunning after an unknown
      draft-creation timeout result.
- [ ] Run the full test suite and commit.

## Phase 5: Validation And Cleanup

- [ ] Review the complete branch diff against the stable baseline.
- [ ] Run all automated tests.
- [ ] Generate and inspect a Preview using test doubles without creating a real draft.
- [ ] Run one complete Draft Run using real Google Sheets and WeChat APIs.
- [ ] Confirm the Draft Run returns a WeChat `media_id`.
- [ ] Confirm the draft exists in the WeChat Official Account backend.
- [ ] Confirm the title, movie count, and Google Sheets row order are correct.
- [ ] Confirm all posters display correctly.
- [ ] Confirm directors, years, ratings, and comments are correct.
- [ ] Confirm `outputs/movie_wechat.html` was generated.
- [ ] Run all automated tests again after real validation.
- [ ] Confirm the stable baseline remains runnable.
- [ ] Delete the unrelated Web App workflow in a separate commit.
- [ ] Update README usage and recovery instructions.
- [ ] Merge only after final approval.
