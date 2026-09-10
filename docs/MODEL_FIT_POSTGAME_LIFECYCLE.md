# Model Fit postgame lifecycle

Performance vs Model is an operator-facing diagnostic. It never changes Standard Spread,
Standard Total, Shadow, ratings, edges, or simulations. Every historical grade
uses the accepted pre-kickoff Standard margin and accepted pre-kickoff close.

The team-game lifecycle is `PREGAME_FROZEN`, `SCORE_READY`, `CFBD_READY`,
`SP_PLUS_READY`, `COMPLETE`, or `DEGRADED`. A final remains pending for 48 hours
before a missing SP+ or CFBD lens is considered degraded. Refreshes retain an
accepted lens through a temporary source omission; an available source row may
revise its own previously accepted value.

Team health is selected-decision-week aware and independent from sample size.
It examines every scheduled FBS game before the selected week: green means the
team's expected prior history is complete, yellow means a prior game is not yet
final or a lens is still inside its 48-hour window, red means required postgame
history is overdue, and gray means no eligible prior sample. An immediately
preceding bye creates no expected game and therefore does not force yellow.
`LOW_SAMPLE`, `DEVELOPING`, and `ESTABLISHED` remain statistical labels only.

For each team-game, `performance_margin` is the equal average of the SP+
adjusted margin and CFBD equivalent margin only when both lenses exist.
`performance_vs_model` is that margin minus the frozen Standard margin and is
the primary diagnostic. `score_vs_model`, `sp_plus_vs_model`, and
`cfbd_vs_model` remain separately interpretable. `display_model_fit` is only a
compatibility alias equal to `performance_vs_model`; a partial combined value is
never fabricated. Rank is signed descending among teams with a complete
two-lens sample; all FBS teams remain present, while no-sample teams have no
rank. Opposite lens signs beyond the 0.1-point near-zero tolerance are labeled
`DISAGREE`.

The existing postgame service performs schedule/final acceptance, refreshes SP+
and CFBD, builds postgame features, rebuilds team-game evaluations, then rebuilds
War Room health and the market matrix. The normal daily flow collects the same
sources before model tracking and rebuilds the matrix during site build, so the
next week's Command Center naturally includes prior-week grades.
