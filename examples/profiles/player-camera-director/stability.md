# Stability

Homeostat for the output stream: prefer stickiness so the committed camera (or
other stream id) does not thrash when scores wobble — including when the host
evaluator is noisy or random.

This example profile uses hysteresis / close-margin style rules in TOML. Not
all stability knobs are fully implemented in every 0.3.x path; see the profile
and engine for what is actually applied.
