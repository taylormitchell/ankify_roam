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
    code {
        border-radius: 5px; 
        -moz-border-radius: 5px; 
        -webkit-border-radius: 5px; 
        border: 1px solid #BCBEC0;
        padding: 2px;
        font:12px Monaco,Consolas,"Andale  Mono","DejaVu Sans Mono",monospace;
    }

    .centered-block{
        display: inline-block;
        text-align: left;
        margin:auto;
    }

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

    pre {
        text-align: left;
        border-radius: 5px;
        border: 1px solid #BCBEC0;
        display: block;
        padding: 10px;
        margin: 0 0 10px;
        font:12px Monaco,Consolas,"Andale  Mono","DejaVu Sans Mono",monospace;
        color: #333;
        background-color: #f5f5f5;
    }

    .back-side.list {
        display: inline-block;
        text-align: left;
    }

    .back-side.list>.block::before {
        content: "•";
        margin-right: 10px;
    }

    .back-side.list>.block {
        margin-left: calc(20px * var(--data-lvl));
    }
"""

_css_breadcrumb_parents = """
    .parent {
        display: inline-block;
        font-size: 10px;
    }
    .parent::after {
        content: "›";
        padding-left: 5px;
        padding-right: 5px;
    }
    .front-side>:not(.parent).block {
        padding-top: 10px;
     }

    .back-side.list {
        display: inline-block;
        text-align: left;
    }

    .back-side.list>.block::before {
        content: "•";
        margin-right: 10px;
    }

    .back-side.list>.block {
        margin-left: calc(20px * var(--data-lvl));
    }
"""

_css_stacked_parents = """
    .front-side, .back-side.list {
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

_css_hide_parents = """
    .parent {
        display: none;
    }
"""

ROAM_BASIC = {
    "modelName": "Roam Basic",
    "inOrderFields": ["Front", "Back", "Extra", "uid"],
    "css": _css_basic+_css_roam,
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
    "inOrderFields": ["Text", "Extra", "uid"],
    "css": _css_cloze+_css_roam,
    "cardTemplates": [
        {
            "Name": "Cloze",
            "Front": "{{cloze:Text}}",
            "Back": "{{cloze:Text}}<br><br>{{Extra}}"
        }
    ]   
}