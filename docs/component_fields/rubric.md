### Rubrics

Rubrics are grading tools that define criteria and achievement levels for assessing student work. Easel supports creating and managing rubrics as independent components that can be associated with assignments.

## Rubric Fields

The following fields are recognized by easel for rubrics. See the [Canvas documentation](https://canvas.instructure.com/doc/api/rubrics.html) for more details.

- `title` (required) - The name of the rubric
- `free_form_criterion_comments` - Allow evaluators to write free-form comments (boolean)
- `criteria` - Array of criterion objects that define the rubric structure
- `points_possible` - Total points possible for the rubric
- `rubric_association` (optional) - Settings for how the rubric is associated with a course or assignment. If not specified, the rubric will be associated with the course by default.

## Rubric Criteria Structure

Each criterion in the `criteria` array should have the following structure:

- `description` - The name/description of the criterion
- `points` - Maximum points for this criterion
- `long_description` - Optional detailed description
- `criterion_use_range` - Whether to use a range for scoring (boolean)
- `ratings` - Array of rating objects for this criterion

Each rating should have:
- `description` - The name of this rating level
- `points` - Points awarded for this rating
- `long_description` - Optional detailed description

## Example Rubric

Create a file in the `rubrics/` directory (e.g., `rubrics/essay_rubric.yaml`):

```yaml
!Rubric
title: Essay Grading Rubric
free_form_criterion_comments: true
points_possible: 20
criteria:
  - description: Thesis Statement
    points: 5
    long_description: Clear, focused thesis that addresses the prompt
    ratings:
      - description: Excellent
        points: 5
        long_description: Thesis is clear, specific, and fully addresses the prompt
      - description: Good
        points: 4
        long_description: Thesis addresses the prompt with minor issues
      - description: Adequate
        points: 3
        long_description: Thesis is present but lacks clarity or focus
      - description: Poor
        points: 2
        long_description: Thesis is unclear or doesn't address the prompt
      - description: Missing
        points: 0
        long_description: No thesis statement present
  - description: Organization
    points: 5
    long_description: Logical flow and structure of ideas
    ratings:
      - description: Excellent
        points: 5
      - description: Good
        points: 4
      - description: Adequate
        points: 3
      - description: Poor
        points: 2
      - description: Missing
        points: 0
  - description: Evidence and Support
    points: 5
    long_description: Use of relevant evidence to support arguments
    ratings:
      - description: Excellent
        points: 5
      - description: Good
        points: 4
      - description: Adequate
        points: 3
      - description: Poor
        points: 2
      - description: Missing
        points: 0
  - description: Grammar and Mechanics
    points: 5
    long_description: Spelling, grammar, punctuation, and formatting
    ratings:
      - description: Excellent
        points: 5
      - description: Good
        points: 4
      - description: Adequate
        points: 3
      - description: Poor
        points: 2
      - description: Missing
        points: 0
```

## Using Rubrics

To push a rubric to your course:

```bash
easel push rubrics/essay_rubric.yaml
```

To pull all rubrics from a course:

```bash
easel pull rubrics
```

To remove a rubric from Canvas:

```bash
easel remove rubrics/essay_rubric.yaml
```

## Notes

- When pulling rubrics from Canvas, the API's `data` field is automatically converted to `criteria` for cleaner YAML representation
- Internal Canvas IDs (like `id`, `criterion_id`) are automatically generated when pushing - you don't need to specify them
- When not specified, rubrics are automatically associated with the course as bookmarks
- Rubrics can be associated with assignments using the assignment's `rubric` and `rubric_settings` fields
