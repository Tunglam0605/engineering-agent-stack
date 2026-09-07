Fix the retry backoff bug with the smallest correct change.

Constraints:
- preserve the public function signature,
- do not change the tests,
- attempt 1 must use the base delay,
- exponential growth must still respect the cap.

Run the relevant tests before finishing.
