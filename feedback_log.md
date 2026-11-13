# Feedback Log

## Early feedback

| Student/tester | Single biggest fix before final |
|---|---|
| P1 | Make the scatter plot's vote-average color encoding explicit so users do not have to infer what the Viridis scale means. |
| P2 | Explain that the genre chart shows the six largest genres individually and groups the remaining genres into `Other`. |

## Changes made

- Added visible guidance that Viridis color encodes vote average.
- Added a caption explaining the grouped `Other` genre category.
- Corrected numeric filtering so missing budget, revenue, year, or rating values are not counted as in-range selections.
- Confirmed that scatter selections update the genre, timeline, rating, and KPI views together, and that **Reset All Filters** restores the full dataset.
