# WeChat Draft Workflow

This context covers creating a WeChat Official Account movie article draft from
movie records stored in Google Sheets.

## Language

**Draft Run**:
One end-to-end invocation that selects movies, uploads posters, renders article HTML, and creates one WeChat draft.
_Avoid_: Preview run, publish run

**Preview**:
The rendered article HTML produced during a Draft Run for inspection and troubleshooting.
_Avoid_: Publish candidate

**Digest**:
The WeChat article summary entered for a Draft Run.
_Avoid_: Description

**WeChat Configuration**:
The complete set of WeChat credentials and article defaults stored in `configs/ids.json`.
_Avoid_: Environment configuration

**Draft Period**:
The year and one-month or two-month range selected for a Draft Run.
_Avoid_: Date filter

**Draft Movie**:
A movie record selected from Google Sheets for inclusion in a Draft Run.
_Avoid_: Sheet row

## Relationships

- A **Draft Run** produces exactly one **Preview**
- The **Preview** is stored at `outputs/movie_wechat.html` and overwritten by each Draft Run
- A successful **Draft Run** creates exactly one WeChat draft
- A **Draft Run** starts immediately after its inputs are collected, without a final confirmation gate
- A **Draft Run** stops before draft creation if any poster upload fails
- A failed **Draft Run** does not preserve poster upload progress for reuse
- An empty **Digest** is sent to WeChat as a single space
- A **Draft Run** reads Google Sheets without creating a local sheet backup
- A **Draft Run** obtains all WeChat credentials and article defaults from **WeChat Configuration**
- A **Draft Period** defaults to the current year or month only when the corresponding input is blank
- Invalid **Draft Period** input ends the Draft Run with a clear error
- A **Draft Period** with no movies ends the Draft Run before poster upload or draft creation
- A **Draft Period** always belongs to one year and does not span across years
- An invalid **Draft Movie** ends the Draft Run and reports its sheet row and missing fields
- A **Draft Movie** requires `date`, `name`, `director`, `year`, `rating`, `comment`, `movie_id`, and `image_id`
- A **Draft Movie** may have an empty `comment`, and `quality` is not required for a Draft Run
- **Draft Movies** retain their Google Sheets row order in the article
- A draft-creation timeout leaves the **Draft Run** result unknown and must not be retried automatically
- A WeChat API business error is displayed using the response returned by WeChat
- A **Draft Run** obtains one WeChat access token and reuses it for poster uploads and draft creation
- An invalid or expired access token is not refreshed and retried automatically
- The unrelated Web App workflow is removed only after the refactored Draft Run is verified

## Example dialogue

> **Dev:** "Should the user run Preview and publication separately?"
> **Domain expert:** "No. One Draft Run should perform the complete workflow."
>
> **Dev:** "What happens if one poster cannot be uploaded?"
> **Domain expert:** "Stop the Draft Run and create no draft. A rerun can upload posters again from the beginning."
>
> **Dev:** "Can the Digest be empty?"
> **Domain expert:** "Yes. Preserve the current workaround and send a single space."
>
> **Dev:** "Where should the WeChat author and thumbnail be configured?"
> **Domain expert:** "Keep all WeChat configuration in configs/ids.json."
>
> **Dev:** "What should happen if the user types a non-integer month?"
> **Domain expert:** "Stop with a clear error. Do not silently use the current month."
>
> **Dev:** "Should an empty Draft Period create an empty draft?"
> **Domain expert:** "No. Stop with a clear error before uploading anything."
>
> **Dev:** "Should a Draft Run skip a movie with missing fields?"
> **Domain expert:** "No. Stop and report the row and missing fields."
>
> **Dev:** "What should happen when draft creation times out?"
> **Domain expert:** "Report that the result is unknown and remind the user to check WeChat before rerunning."
>
> **Dev:** "How should a WeChat API business error be displayed?"
> **Domain expert:** "Show the response returned by WeChat directly."
>
> **Dev:** "Should a Draft Run request a new access token before draft creation?"
> **Domain expert:** "No. Reuse one token for the complete Draft Run."
>
> **Dev:** "When should the unrelated Web App workflow be removed?"
> **Domain expert:** "After the refactored Draft Run has been verified, in a separate change."

## Flagged ambiguities

- "Preview" previously implied a possible separate command; resolved: it is an output of a Draft Run, not a separate workflow.
- "Explicit human confirmation" previously implied a final publication gate; resolved: a Draft Run executes immediately after input collection.
- "Poster upload cache" was considered for failed reruns; resolved: no cache is needed for now.
- "Preview history" was considered for traceability; resolved: keep one fixed Preview file and overwrite it on each Draft Run.
- "Google Sheets backup" previously described a local copy written during reads; resolved: remove it because the Draft Run does not modify Google Sheets.
- "WeChat configuration source" previously mixed file-based values and hard-coded values; resolved: all WeChat configuration belongs in `configs/ids.json`.
- "Required Draft Movie fields" excludes `quality`; `comment` must be present but may be empty.
- "Draft creation timeout" is not treated as a definite failure; resolved: report an unknown result, do not auto-retry, and remind the user to inspect WeChat.
- "WeChat API error formatting" does not add a custom business-error message; resolved: display the WeChat response directly.
- "Access token reuse" previously requested separate tokens for upload and draft creation; resolved: use one token per Draft Run without automatic refresh.
- "Cross-year Draft Period" is not a supported business scenario; resolved: preserve the current same-year title rules.
- "Draft Movie ordering" is controlled by Google Sheets row order; resolved: the Draft Run does not sort movies.
- "Web App removal timing" is resolved: remove it after Draft Run verification in a separate commit.
