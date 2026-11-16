"""Research ablation: disable ticket-delay override, leaving reference intact.

For the sequential benchmark only: scoped patching is not thread-safe.
The reference still makes the same MockLLM calls with the same prompts.
The variant retains reference run IDs; benchmark rows identify the arm.
"""

from unittest.mock import patch

from lab8.shapes import swarm_reference


def run_claim(claim_id, *, seed, store_path, crash_at=None):
    # Returning None only disables use of parsed ticket delay in the quote.
    # mock_llm.complete still parses the same prompt internally as before.
    with patch.object(swarm_reference, "parse_delay_days", return_value=None):
        return swarm_reference.run_claim(
            claim_id, seed=seed, store_path=store_path, crash_at=crash_at,
        )
