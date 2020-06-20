# Ankify Roam

A command-line tool for importing flashcards from Roam into Anki.

<table>
<tr>
<td width=300px>
    <img src="images/roam_screenshot.png">
</td>
<td><div>→</div></td>
<td width=300px>
    <div>
        <img src="images/anki_screenshot.png">
    </div>
</td>
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

Define a card by adding the #ankify tag. By default the block will be converted into a Basic card with the block content on the front and it's children on the back: 

- What is the capital of France? #ankify
    - Paris

You can also create cloze deletions with curly brackets. If the block tagged with #ankify has any cloze deletions, then it'll be converted to a Cloze card. You can explicitely define the cloze ids or have ankify_roam infer them. Here's an example of cloze markup in Roam and what it becomes in Anki:

<table width=500px>
<tr>
    <td>
        <div>{1:Paris} is the capital and most populous city of {2:France}, with a estimated population of {2,148,271} residents #ankify</div>
    </td>
</tr>
<tr>
    <td align="center">↓<td>
</tr>
<tr>
    <td>
        <div>{{c1::Paris}} is the capital and most populous city of {{c2::France}}, with a estimated population of {{c3::2,148,271}} residents #ankify</div>
    </td>
</tr>
</table>

### 2. Export Roam

Once you've tagged all the blocks to ankify, export your Roam: 
1. Click on the ... in the top right corner
2. Select Export All > JSON > Export All
3. Unzip the downloaded file.

### 3. Open Anki

Open Anki. Make sure you're on the profile you'd like to add the cards to and that you've installed the anki_connect plugin.

### 4. Create Roam specific card types 

Running the following will create 2 new card types in anki for your Roam flashcards: 'Roam Basic' and 'Roam Cloze'
```
ankify_roam init
```
### 5. Add the Roam export to Anki

```
ankify_roam add my_roam.json
```
The blocks you tagged in Roam should now be in Anki!

### 6. Repeat

When you tag new blocks to ankify or edit ones you've already imported to Anki, you'll need to export your database again, and then rerun `ankify_roam add` on the export. This will add any newly tagged blocks and update the existing ones with any changes you've made.  

## Features

Instead of specifying the Roam export json, you can specify the exported zip file or give the directory it's in and ankify_roam will add the latest export in there.
```
akrm add Roam-Export-1592525007321.zip
akrm add ~/Downloads
```

Use a different tag than #ankify:
```
akrm add --tag-ankify=flashcard my_roam.json
```  

Use different note types than 'Roam Cloze' and 'Roam Basic':
```
akrm add --default-basic="My Basic" --default-cloze="My Cloze" my_roam.json
``` 
Same thing for the deck to add to:
```
akrm add --deck="Biology" my_roam.json
```
Specify the deck and note type on a per-card basis: 

- 2+2={4} #[[[[ankify]]:deck=Math]] #[[[[ankify]]:model=My Cloze]]


## Fancy stuff

### Styling the cloze markup

Instead of using curly brackets to define, you can use page links:

.rm-page-ref-brackets {
    color: #a7b6c2;
}

.rm-page-ref-link-color {
    color: #106ba3;
}

.rm-page-ref-tag {
    color: #a7b6c2;
}
<blockquote>
[[(]]Paris[[)]] is the capital and most populous city of [[(]]France[[)]] #ankify
</blockquote>

The nice thing about doing it this way is that you can now style the cloze markup:
1. Press `Ctrl-C Ctrl-B` in Roam to hide page link square brackets.
2. Add this css to your [[roam/css]] page to change the color of the curly brackets:
```css
span[data-link-title="{"] > span,
span[data-link-title="}"] > span
{
  color: #DDDCDC !important;
}
```

Now your cloze markup will look like this:
<blockquote>
<span style="color:#DDDCDC">{</span>Paris<span style="color:#DDDCDC">}</span> is the capital and most populour city of <span style="color:#DDDCDC">{</span>France<span style="color:#DDDCDC">}</span> #ankify
</blockquote>

<span style="color:#DDDCDC">{</span>Paris<span style="color:#DDDCDC">}</span> is the capital and most populour city of <span style="color:#DDDCDC">{</span>France<span style="color:#DDDCDC">}</span> #ankify


TODO: fancy cloze markup

TODO: pageref_cloze

TODO: styling roam. hide tags. hide brackets. Hide bullets. probably need separate page.

TODO: how to create your own note type

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