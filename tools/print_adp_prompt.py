"""Print one fictional prompt through the production adapter, with no network or credentials.

Run from the repository: PYTHONPATH=src python tools/print_adp_prompt.py
The fake transport captures Contents[0].Text unchanged. No reply is generated.
"""
from carerelay import adp_extraction as adp
from carerelay.demo.fixture import policy


def fictional_prompt() -> str:
    prompts = []

    class Capture:
        provenance = "fake-offline"

        def open(self, endpoint, body, *, deadline_monotonic, allow_redirects):
            prompts.append(body["Contents"][0]["Text"])
            return adp.TransportResponse(200, ())

    fixture = policy()
    request = adp.ExtractionInput(
        "Myself, today before 6pm, I'll see the doctor",
        frozenset(fixture.action_aliases) | fixture.permitted_action_ids,
        frozenset(fixture.deadline_forms),
        frozenset(fixture.owner_aliases) | fixture.permitted_owner_ids,
        "fictional-console-diagnosis-21", adp.LIVE_INSTRUCTION, adp.SCHEMA_VERSION,
    )
    extractor = adp.AdpReadbackExtractor(
        transport=Capture(), profile="fake-complete-v1",
        endpoint="http://127.0.0.1/offline-prompt",
        app_key="offline-placeholder-not-a-credential", enabled=True,
    )
    # Both profiles construct the prompt in the same extract method before framing.
    extractor.extract(request)
    if len(prompts) != 1:
        raise RuntimeError("Offline adapter did not produce exactly one prompt")
    return prompts[0]


if __name__ == "__main__":
    print(fictional_prompt())
