# Course Deliverable Screenshots

Drop a screenshot of each artifact into this folder using the filename listed
below. The build script (`scripts/build_site.py`) checks for each file at
build time and only renders the thumbnail tile on cards whose screenshot is
present — so cards without a matching file still render cleanly with just
the icon + content.

| File | Artifact |
|---|---|
| `deliverable-accessibility-resources.png` | AIL-608 Accessibility Resources Portfolio (Google Sites) |
| `deliverable-accessibility-audit.png` | AIL-608 Accessibility Audit of Adobe Express (Slides) |
| `deliverable-graphic-design-analysis.png` | AIL-690 Graphic Design Analysis (Slides) |
| `deliverable-tec-variety.png` | AIL-602 Strategies–Materials Mapping (TEC-VARIETY) |
| `deliverable-storyboard.png` | AIL-605 Storyboard for Two-Dimensional Geometrical Shapes |
| `deliverable-multimedia-proposal.png` | AIL-605 Interactive Multimedia Proposal |
| `deliverable-infographic-self.png` | AIL-689 Infographic Self-Presentation |

## Image guidelines

- **Aspect ratio**: any 16:10 or wider works best (the card crops to 16:10
  with `object-fit: cover`). 16:9 also looks great.
- **Resolution**: 1200–1600 px wide is plenty. Bigger than 1600 wastes bytes.
- **Format**: PNG is fine; JPG works too — just keep the filename `.png`
  in the data, or update the entry in `PORTFOLIO_COURSE_DELIVERABLES`.
- **Content**: a clean screenshot of the artifact's most representative
  view (the Google Site home, the first audit-summary slide, the storyboard
  overview, etc.). The build applies a subtle navy duotone tint on top so
  the seven cards read as one cohesive grid.
