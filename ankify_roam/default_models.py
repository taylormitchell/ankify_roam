import textwrap 
from ankify_roam import anki


_css_basic = """
    .card {
        font-family: arial;
        font-size: 20px;
        text-align: center;
        color: black;
        background-color: white;
    }
"""

_css_cloze = """
    .card {
        font-family: arial;
        font-size: 20px;
        text-align: center;
        color: black;
        background-color: white;
    }

    .cloze {
        font-weight: bold;
        color: blue;
    }

    .nightMode .cloze {
        color: lightblue;
    }
"""

_css_roam = """
    /* Code */

    code {
        border-radius: 5px; 
        border: 1px solid #BCBEC0;
        padding: 2px;
        font:12px Monaco,Consolas,"Andale  Mono","DejaVu Sans Mono",monospace;
    }

    pre code {
        border-radius: 5px;
        border: 1px solid #BCBEC0;
        padding: 10px;
        font:12px Monaco,Consolas,"Andale  Mono","DejaVu Sans Mono",monospace;
        text-align: left;
        display: block;
        margin: 0 0 10px;
        color: #333;
        background-color: #f5f5f5;
    }

    /* Roam markup */

    .rm-page-ref-brackets {
        color: #a7b6c2;
    }

    .rm-page-ref-link-color {
        color: #106ba3;
    }

    .rm-page-ref-tag {
        color: #a7b6c2;
    }

    .rm-block-ref {
        padding: 2px 2px;
        margin: -2px 0px;
        display: inline;
        border-bottom: 0.5px solid #d8e1e8;
        cursor: alias;
    }

    .roam-highlight {
        background-color: #fef09f;
        margin: -2px;
        padding: 2px;
    }

    .bp3-button.bp3-small, .bp3-small .bp3-button {
        min-height: 24px;
        min-width: 24px;
        padding: 0 7px;
    }

    .rm-bq {
        background-color: #F5F8FA;
        border-left: 5px solid #30404D;
        font-size: 14px;
        margin: 0 0 10px;
        word-wrap: break-word;
    }

    blockquote {
        padding: 10px 20px;
    }

    /* ankify_roam markup */

    [data-tag="ankify"], [data-tag^="[[ankify]]:"], [data-tag^="ankify_roam:"], [data-tag^="[[ankify_roam]]:"]{
      display:none;
    }

    /* Align bullet to top of content*/
    li > * {
        vertical-align: text-top;
    }

    .front-side ul {
        display: inline;
        list-style-type: none;
        margin: 0;
        padding: 0;
    }

    .back-side ul {
        text-align: left;
        list-style-type: disc;
    }

    .back-side.single ul {
        text-align: center;
        margin: 0;
        padding: 0;
        list-style-type: none;
    }
"""

_css_breadcrumb_parents = """
    .parent {
        display: inline-block;
        font-size: 15px;
        opacity: 0.5;
    }

    .parent::after {
        content: "›";
        padding-left: 5px;
        padding-right: 5px;
    }

    .front-side :not(.parent).block {
        padding-top: 20px;
     }
"""

_css_stacked_parents = """
    .front-side {
        display: inline-block;
        text-align: left;
    }
    
    .front-side.block::before {
        content: "•";
        margin-right: 10px;
    }
    .front-side.block {
        margin-left: calc(20px * var(--data-lvl));
    }
"""

ROAM_BASIC = {
    "modelName": "Roam Basic",
    "inOrderFields": ["Front", "Back", "Extra", "uid"],
    "css": textwrap.dedent(_css_basic+_css_roam+_css_breadcrumb_parents),
    "cardTemplates": [
        {
            "Name": "Card 1",
            "Front": "{{Front}}",
            "Back": "{{FrontSide}}<hr id=answer>{{Back}}<br><br>{{Extra}}"
        }
    ]   
}

ROAM_CLOZE = {
    "modelName": "Roam Cloze",
    "inOrderFields": ["Text", "Back Extra", "uid"],
    "css": textwrap.dedent(_css_cloze+_css_roam+_css_breadcrumb_parents),
    "cardTemplates": [
        {
            "Name": "Cloze",
            "Front": "{{cloze:Text}}",
            "Back": "{{cloze:Text}}<br>\n{{Back Extra}}"
        }
    ]   
}


def add_default_models(overwrite=False):
    res = {}
    for model in [ROAM_BASIC, ROAM_CLOZE]:
        modelNames = anki.get_model_names()
        name = model['modelName']
        if not name in modelNames:
            res[name] = anki.create_model(model)
        elif overwrite:
            res[name] = anki.update_model(model)
        else:
            res[name] = None
    return res
