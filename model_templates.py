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
    font:12px Monaco,Consolas,"Andale  Mono","DejaVu Sans Mono",monospace
}

.centered-block{
    display: inline-block;
    align: center;
    text-align: left;
    marge:auto;
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
"""

roam_basic = {
    "modelName": "Roam Basic",
    "inOrderFields": ["Front", "Back", "Extra", "uid"],
    "css": _css_basic+_css_roam,
    "cardTemplates": [
        {
            "Name": "Card 1",
            "Front": "{{Front}}",
            "Back": "{{FrontSide}}<hr id=answer>{{Back}}<br>{{Extra}}"
        }
    ]   
}

roam_cloze = {
    "modelName": "Roam Cloze",
    "inOrderFields": ["Text", "Extra", "uid"],
    "css": _css_cloze+_css_roam,
    "cardTemplates": [
        {
            "Name": "Card 1",
            "Front": "{{cloze:Text}}",
            "Back": "{{cloze:Text}}<br>{{Extra}}"
        }
    ]   
}