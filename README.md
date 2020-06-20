# Ankify Roam

A command-line tool for importing flashcards from Roam into Anki.

<table border=1px>
<tr>
    <td width=350px>
        <b>Geography</b>
        <ul>
        <li>What is the <span data-link-title="capital"><span class="rm-page-ref-brackets">[[</span><span tabindex="-1" class="rm-page-ref rm-page-ref-link-color">capital</span><span class="rm-page-ref-brackets">]]</span></span> of <span data-link-title="France"><span class="rm-page-ref-brackets">[[</span><span tabindex="-1" class="rm-page-ref rm-page-ref-link-color">France</span><span class="rm-page-ref-brackets">]]</span></span>? <span tabindex="-1" data-tag="ankify" class="rm-page-ref rm-page-ref-tag">#ankify</span></li>
        <ul><li>Paris</li></ul>
        </ul>
<tr>
    <td width=350px align="center">
        <div>|</div>
        <div>Ankify!</div>
        <div>↓</div>
    </td>
<tr>
<tr>
    <td width=350px>
        <div align="center">
        <div>What is the <span data-link-title="capital"><span class="rm-page-ref-brackets">[[</span><span tabindex="-1" class="rm-page-ref rm-page-ref-link-color">capital</span><span class="rm-page-ref-brackets">]]</span></span> of <span data-link-title="France"><span class="rm-page-ref-brackets">[[</span><span tabindex="-1" class="rm-page-ref rm-page-ref-link-color">France</span><span class="rm-page-ref-brackets">]]</span></span>? <span tabindex="-1" data-tag="ankify" class="rm-page-ref rm-page-ref-tag">#ankify</div>
        <hr id=answer>
        <div>Paris</div>
        <div>
    </td>
</tr>
<tr>
    <td>Tags: capital, France, Geography</td>
</tr>
</table>


## Installation

```
pip install ankify_roam
```

## Requirements

- Python >=3.6
- Anki
- AnkiConnect
    - Open the Install Add-on dialog by selecting Tools | Add-ons | Browse & Install in Anki.
    - Input 2055492159 into the text box labeled Code and press the OK button to proceed.
    - Restart Anki when prompted to do so in order to complete the installation of AnkiConnect.

## Getting Started

### 1. Ankify Roam
In Roam, tag blocks which you want to import to anki with #ankify:


- What is the capital of France? #ankify
    - Paris


If the tagged block includes cloze deletion, then it'll become a Cloze card. You can explicitely define the cloze ids or have ankify_roam infer them. Here's an example of cloze markup in Roam and what it becomes in Anki:

<table width=500px>
<tr>
    <td>
        <div>{1:Paris} is the capital and most populous city of {2:France}, with a estimated population of {2,148,271} residents as of {2020}, in an area of {105} square kilometres #ankify</div>
    </td>
</tr>
<tr>
    <td align="center">↓<td>
</tr>
<tr>
    <td>
        <div>{{c1:Paris}} is the capital and most populous city of {{c2:France}}, with a estimated population of {{c3:2,148,271}} residents as of {{c4:2020}}, in an area of {{c5:105}} square kilometres #ankify</div>
    </td>
</tr>
</table>

### 2. Export Roam

Once you've tagged all the blocks to ankify, export your Roam: 
1. Click on the ... in the top right corner
2. Select Export All > JSON > Export All
3. Unzip the downloaded file.

### 3. Open Anki

Open Anki. Make sure you've installed the anki_connect plugin.

### 4. Create Roam specific card types 

Running the following will create 2 new card types in anki for your Roam flashcards: 'Roam Basic' and 'Roam Cloze'
```
akrm init
```
### 5. Add the Roam export to Anki

```
akrm add my_roam.json
```
The blocks you tagged in Roam should now be in Anki!

### 6. Create new cards and edit existing ones

When you tag new blocks to ankify or edit ones you've already imported to Anki, you'll need to export your database again, and then rerun `akrm add` on the export. This will add the newly tagged blocks and update the existing ones.  

## Features

Instead of specifying the Roam export json, you can specify the exported zip file or give the directory it's in and ankify_roam will add the latest export in there.
```
akrm add Roam-Export-1592525007321.zip
akrm add ~/Downloads
```

Use a different tag than #ankify to flag blocks. Just tell ankify_roam what it is:
```
akrm add --tag-ankify=flashcard my_roam.json
```  

Create your own Anki note types and tell ankify_roam to use those instead of 'Roam Cloze' and 'Roam Basic':
```
akrm add --default-basic="My Basic" --default-cloze="My Cloze" my_roam.json
``` 
Same thing for the deck which the cards are added to:
```
akrm add --deck="Biology" my_roam.json
```
You can also specify the deck and note type on a per-card basis using tags/page-refs. 

- 2+2={4} #ankify #[[[[akrm]]:deck=Math]] #[[[[akrm]]:model=My Cloze]]

If a block specifies the deck and/or model like the above, then ankify_roam will use those instead of the default options you provid at the command line. 


TODO: block refs

TODO: images 

## Fancy stuff

TODO: fancy cloze markup

TODO: pageref_cloze

TODO: styling roam. hide tags. hide brackets. Hide bullets. probably need separate page.

## Documentation 

### Description

You can run `ankify_roam` on the Roam export zip, the json inside, or the folder containing the zip export:

- from json: `ankify_roam roam_export.json`
- from zip: `ankify_roam Roam-Export-1592174304830.zip`
- latest zip in folder: `ankify_roam ~/Downloads/`

### Options

--default-deck

--default-basic

--default-cloze


<style>
/*
table {
    width:100%;
    border:none;
}
*/
.table-cell {
    width:350px;
}
.card {
 font-family: arial;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
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

</style>