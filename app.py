import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
from typing import Iterable, List, Dict
import itertools
import yaml
import pandas as pd
import textwrap
from code_editor import code_editor

TAGS = [
    "data_collection",
    "data_processing",
    "feature_extraction",
    "statistical_analysis",
    "other",
]

COLORS = ["pink", "lightblue", "lightgreen", "yellow", "orange"]


def powerset(a: Iterable) -> Iterable[Iterable]:
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(a)
    return [
        ",\n".join(x)
        for x in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def range_inclusive(a: Dict) -> Iterable:
    return list(range(a.get("min"), a.get("max") + 1, a.get("step", 1)))


def validate_one(d):
    try:
        assert isinstance(d, dict)
        assert "name" in d
        assert "tag" in d
        assert d["tag"] in TAGS
        assert "choices" in d
        if isinstance(d["choices"], dict):
            assert "min" in d["choices"]
            assert "max" in d["choices"]
        else:
            assert len(d["choices"])
    except AssertionError as e:
        print(f">>Formatting error in choicepoint `{d['name']}`")
        raise e
    return True


def validate_all(d):
    assert isinstance(d, list)
    names = [item["name"] for item in d]
    assert len(names) == len(set(names))
    results = list(map(validate_one, d))
    assert all(results)


# set wide layout
st.set_page_config(layout="wide")

example = """# The following is an example YAML specification involving 3 choice points
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
"""

st.title("Tracking Experimenter Degrees of Freedom")
st.markdown(
    """*Scroll down for more detailed instructions*

This tool was created as a class project for 9.401: Tools for Robust Science. 

The purpose of this tool is to allow researchers to more easily track and visualize the choices 
they make as part of a research project. 

In any experiment, study, or analysis, researchers make choices - some big, some small - 
that may impact the final results. Some of these choices may seem minor or inconsequential,
while some choices may be made on the spot without much deliberation. 
One problem often cited as a barrier to robustness is the combinatorial explosion of these choice points: 
given the huge space of possible choices, it's unlikely that two independent researchers will make
the same choices to address the same question. 
We hope that this tool will help people track their choices, 
maintain an awareness of what choices they are exploring vs. not exploring, 
and share their choices with intended audiences. 

Feel free to contact `thclark @ mit . edu` to give your feedback on this tool. 
"""
)

# text = st.text_area("Enter text in YAML format", value=example, height=400,)
st.markdown(
    """
### Enter description of choices in YAML format
Press Command-Enter to apply changes in text area"""
)
response_dict = code_editor(example, lang="yaml")
text = response_dict["text"]
if text == "":
    text = example
print(response_dict)

# Load the choices from the YAML file and validate
d = list(yaml.load_all(text, yaml.Loader))
validate_all(d)

# handle keywords (powerset, range, etc.)
for item in d:
    if item.get("choices_operation") == "powerset":
        item["choices"] = powerset(item["choices"])
    elif item.get("choices_operation") == "range":
        item["choices"] = range_inclusive(item["choices"])
    if item.get("rejected_choices"):
        item["choices"] = list(
            set(item["choices"]) - set([x["name"] for x in item["rejected_choices"]])
        )

all_choices = list(itertools.product(*[item["choices"] for item in d]))

net = Network(
    height="750px", width="100%", bgcolor="#white", font_color="black", layout=True
)

color_mapping = dict(zip(TAGS, COLORS))

# add nodes to graph
for i, item in enumerate(d):
    for choice in item["choices"]:
        tag = item["tag"]
        desc = "\n".join(
            textwrap.wrap(item.get("description", "TODO: No Description Provided"))
        )
        box_text = f"Tag: {tag}\n\n{desc}"
        net.add_node(
            f"<b>{item['name']}</b>\n{choice}",
            level=i,
            title=box_text,
            color=color_mapping.get(item["tag"]),
            shape="box",
        )
    # for choice in item.get("rejected_choices", set()):
    #     net.add_node(
    #         f"{item['name']}\n{choice['name']}",
    #         level=i,
    #         title="\n".join(
    #             textwrap.wrap(item.get("description", "TODO: No Description Provided"))
    #         ),
    #         color="lightgray",
    #         shape="box",
    #     )

# names = [item["name"] for item in d]

# add edges to graph
for a, b in zip(d[:-1], d[1:]):
    for c, d in itertools.product(a["choices"], b["choices"]):
        net.add_edge(
            f"<b>{a['name']}</b>\n{c}", f"<b>{b['name']}</b>\n{d}", color="gray"
        )

# graph style
s = """
const options = {
  "nodes": {
    "borderWidth": null,
    "borderWidthSelected": null,
    "opacity": null,
    "size": 32,
    "font": {
        "size": 32,
        "multi": "html"
    }
  },
  "edges": {
    "color": {
      "inherit": true
    },
    "selfReferenceSize": null,
    "selfReference": {
      "angle": 0.7853981633974483
    },
    "smooth": {
      "type": "horizontal",
      "forceDirection": false
    }
  },
  "layout": {
    "hierarchical": {
      "enabled": true
    }
  },
  "physics": {
    "hierarchicalRepulsion": {
      "centralGravity": 0,
      "nodeDistance": 200,
      "avoidOverlap": 1
    },
    "minVelocity": 0.75,
    "solver": "hierarchicalRepulsion"
  }
}
"""
net.set_options(s)

net.show("graph.html", notebook=False)

HtmlFile = open("graph.html", "r", encoding="utf-8")
source_code = HtmlFile.read()

st.markdown(
    """### Visualization
Hover on a node to view more information.
Right-click on this image to save it as a PNG."""
)
components.html(source_code, height=600, width=800)

st.markdown(f"### Number of paths through choice space: :orange[{len(all_choices)}]")

st.markdown("## Instructions")
st.markdown(
    """The following is an example of the YAML specification for a single experimenter choice point. 
    Specifications for different choice points are separated by triple-dashes (`---`). 
    The `name`, `tag`, and `choices` fields are required. 
    Each choice point corresponds to a single level of the graph visualization, 
    while each choice value within the `choices` field corresponds to a node at that level.
    Each unique path through the network represents a unique combination of experimenter choices."""
)
ex1 = """
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
"""
st.code(ex1, language="yaml")

st.markdown(
    """### Tags
The following tags are possible: `data_collection`, `data_processing`, `feature_extraction`, `statistical_analysis`, `other`. 
Nodes in the visualization are color-coded by tag.
"""
)

st.markdown(
    """### Descriptions
Provide a plain-text description of the meaning of this choice point, and any relevant information. 
These descriptions will appear on hover over the nodes in the visualization. 
"""
)

st.markdown(
    """### Special Operators
Several special operators are provided for quickly generating choice options.
These are invoked using the optional `choices_operation` field. Options are `powerset` and `range`.
The `powerset` operator adds every possible subset of the provided choices as a choice. 
For example, if a choice point revolves around which combination of covariates X, Y, and Z to include in an analysis,
then this can easily generate the list of choices `[], [X], [Y], [Z], [X, Y], [X, Z], [Y, Z], [X, Y, Z]`.  
"""
)

ex2 = """
---
name: covariates
tag: statistical_analysis
choices:
  - word_freq
  - previous_prosody
  - gender
choices_operation: powerset
"""
st.code(ex2, language="yaml")

st.markdown(
    """The `range` operator adds a range of values between a minimum and maximum numerical value to the choices. 
When this operator is invoked, the `choices` field is expected to contain `min` and `max` keys with associated values,
and optionally a `step` key (default is 1). 
For example, if an analysis revolves around a sweep of different model parameters, this operator can
easily generate the desired range of values.  
"""
)

ex3 = """
---
name: context_turns
tag: feature_extraction
choices:
  min: 0
  max: 5
  step: 1
choices_operation: range
"""
st.code(ex3, language="yaml")

st.markdown(
    """### Limitations
- Currently, this tool does not yet support choice points that are dependent on other choices. 
"""
)

