# milestone-fixture-bakery

A tiny deliverable used to test [Milestone](https://github.com/imshivamb)'s code verifier.
Not a real bakery.

- `v-pass`: does what the brief asks.
- `v-fail-hidden`: hard-codes the answer the visible test expects, so hidden tests catch it.
- `v-malicious`: the hard-coded version that also tries to read hidden tests, forge test
  results, read secrets and reach the internet. Milestone's sandbox must stop all of it.

Run: `PORT=8000 SMTP_PORT=2525 python app.py`
