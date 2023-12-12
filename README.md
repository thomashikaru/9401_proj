# Tracking Experimenter Degrees of Freedom

The tool is live at [research-choices.streamlit.app](research-choices.streamlit.app)

```yaml
# The following is an example YAML specification involving 3 choice points
---
name: lm
tag: feature_extraction
description: >
  The choice of language model.
  Language models can vary based on number of parameters,
  amount of training data, and other features.
choices:
  - distilgpt
  - gpt2
  - gpt2-medium
---
name: context_length
tag: feature_extraction
description: >
  How many turns of context, prior to the current one, to include
  as input to the model when computing surprisals.
choices:
  min: 0
  max: 5
  step: 1
choices_operation: range
---
name: stats_model
tag: statistical_analysis
choices:
  - lm
  - lmer
description: >
  What statistical model family to use. The `lm` option is a simple linear regression. 
  The `lmer` option is a linear mixed-effects regression.
```
