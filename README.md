# Ankify Roam

A command-line tool which brings flashcards created in [Roam](https://roamresearch.com/) to [Anki](https://apps.ankiweb.net/).

<img src="images/anki_roam_screenshot.png">


## Main Features

- Create Front/Back and Cloze deletion flashcards. 
- Make changes to flashcards you've already imported from Roam and bring those changes over to Anki. 
- Supports block references, images, and aliases.
- Add style to your Anki cards just like in Roam.
- Option to individually specify the deck and note type on each flashcard in Roam.
- Change the color or hide the cloze deletion markup in Roam.

## Contents
1. [Installation](#Installation)
1. [Requirements](#Requirements)
1. [Basic Usage](#Basic-Usage)
1. [Options](#Options)
1. [Customizations](#Modifications)



## Installation

```
pip install ankify_roam
```

## Requirements

- Python >=3.6
- [Anki](https://apps.ankiweb.net/)
- [AnkiConnect](https://github.com/FooSoft/anki-connect) (add-on for Anki)

## Basic Usage

### 1. Ankify Roam

Define a card by adding the #ankify tag. By default the block will be converted into a Front/Back flashcard with the block content on the front and it's children on the back: 

> - What is the capital of France? #ankify
>     - Paris

Use curly brackets to define cloze deletions. Whenever a block tagged with #ankify includes a cloze deletion, ankify_roam converts it to a cloze flashcard. 

> {Paris} is the capital and most populous city of {France}, with a estimated population of {2,148,271} residents #ankify

You can explicitly define the cloze ids or have ankify_roam infer them. Here's an example showing what cloze markup in Roam becomes in Anki:


<table border=0px>
<tr>
<td>
        <div>{Paris} is the capital and most populous city of {2:France}, with a estimated population of {2,148,271} residents #ankify</div>
</td>
<td><div>→</div></td>
<td>
    <div>
        <div>{{c1::Paris}} is the capital and most populous city of {{c2::France}}, with a estimated population of {{c3::2,148,271}} residents #ankify</div>
    </div>
</td>
</tr>
</table>


### 2. Export Roam

Once you've tagged all the blocks to ankify, export your Roam: 
1. Click on the ... in the top right corner
2. Select Export All > JSON > Export All
3. Unzip the downloaded file.

### 3. Open Anki

Open Anki. Make sure you're on the profile you'd like to add the cards to and that you've installed the [AnkiConnect](https://github.com/FooSoft/anki-connect) add-on.

### 4. (First time only) Create Roam specific note types 

Run the following to create 2 new note types in Anki for your Roam flashcards: 'Roam Basic' and 'Roam Cloze'
```
ankify_roam init
```
### 5. Add the Roam export to Anki

```
ankify_roam add my_roam.json
```
The blocks you tagged in Roam should now be in Anki!

### 6. Repeat

When you tag new blocks to ankify or edit ones you already have, updating Anki to reflect the changes will require you to export your database again, and then rerun `ankify_roam add` on the export. This will create new flashcards for any newly tagged blocks and update existing ones with any changes you've made in Roam.  

## Options

#### Roam Export

The Roam export path can refer to the json, the zip containing the json, or the directory which the zip is in. When a directory is given, ankify_roam find and add the latest export in it.
```
ankify_roam add my_roam.json
ankify_roam add Roam-Export-1592525007321.zip
ankify_roam add ~/Downloads
```

#### Ankify Tag, Default Deck, and Default Models

Use a different tag than #ankify to flag flashcards:
```
ankify_roam add --tag-ankify=flashcard my_roam.json
```  

Use different note types than 'Roam Cloze' and 'Roam Basic' (see [Custom Anki note types](#Custom-Anki-note-types) for more details) 
```
ankify_roam add --default-basic="My Basic" --default-cloze="My Cloze" my_roam.json
``` 
Same thing for the deck to add the flashcards to:
```
ankify_roam add --deck="Biology" my_roam.json
```

You can also specify the deck and note type on a per-card basis: 

- 2+2={4} #[[[[ankify]]:deck=Math]] #[[[[ankify]]:model=My Cloze]]

#### Uncloze Namespace

When you add a cloze deletion around a namespaced page reference, eg. 

<img src="images/pageref_cloze_roam.png" width=600px>

... you can tell ankify_roam to only cloze delete the base name part of the page reference, leaving out the namespace, eg.

<img src="images/pageref_cloze_anki.png" width=500px>

... by setting the `--pageref-cloze` option to "base_only":
```
ankify_roam add --pageref-cloze=base_only my_roam.json
```

## Customizations

### Create custom note types

As mentioned [options](#Options) section, you can import to different note types than the default 'Roam Basic' and 'Roam Cloze' types provided. Those note types will need to satisfy 2 requirements to be compatible with ankify_roam:   

1. **Include at least 2 fields for the basic note type and 1 for the cloze**. When ankify_roam is converting a block into an Anki note, it takes the content of the block and places it into the first field of the Anki note. In the case of a Basic type, the children of the block are added to the second field of the Anki note. 

1. **Include an additional field called "uid"**. In addition to those fields, a "uid" field is used by ankify_roam to remember which block in Roam corresponds with which note in Anki. Without this field, when you make a change to a block in Roam, ankify_roam will add that block as a new note in Anki rather than updating the existing one.

If you are going to use your own note types, I'd suggest creating copies of the 'Roam Basic' and 'Roam Cloze' types provided and then modifying those.

### CSS ideas for your Anki cards

Hide all Roam tags (eg. the #ankify tag)
```
.rm-page-ref-tag {
    display: none;
}
```

Hide page reference brackets
```
.rm-page-ref-brackets {
    display: none;
}
```

Hide bullet points to simulate "View as Document" in Roam:
```
li {
    list-style-type: none;
}
```


### Add color or hide cloze deletions in Roam

You can also use curly brackets in page links to define cloze deletions:

<img src="images/page_link_clozes.png" width=600px>

The nice thing about doing it this way is that you can now style the cloze markup. 

For example, you can make the cloze brackets only faintly visible by:
1. Pressing `Ctrl-C Ctrl-B` in Roam to hide the square brackets surrounding page links.
2. Adding this css to your [[roam/css]] page (how to [video here](https://www.youtube.com/watch?v=UY-sAC2eGyI)) to change the color of the curly brackets:
```css
span[data-link-title="{"] > span,
span[data-link-title="}"] > span
{
  color: #DDDCDC !important;
}
```

Now the block shown above will look like this: 

<img src="images/page_link_clozes_better.png" width=600px>



