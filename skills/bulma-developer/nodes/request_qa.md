# Node: request_qa

**Verb:** switch or enqueue  
**Capability:** write bus only

For single delivery and the QA-enabled umbrella, run after CI green,
MERGEABLE, and **bot_review** skip or pass. A child of a stack returns to
**stack** without creating a QA request. The umbrella uses the parent
acceptance and the current integrated SHA. Apply the usual external
provider and evidence rules.

Write `QA_REQUEST` ([../references/QA_HANDOFF.md](../references/QA_HANDOFF.md))
to `.bulma-bus/jobs/<job_id>/qa-request.md`. PR link + `job_id` required.

Then **Enqueue or start QA** (`bulma-bus/JOBS.md`):

- Slot free → copy to `ENVELOPE.md`, bus switch to `qa`.
- Slot taken → append `qa_waiting`. Do not switch. Do not
  spawn `bulma_qa`. Tell the user their queue position (in English).

QA must still comment with evidence (UI video, or HTTP still /
FE screens of callers) before **this job** is done.
