# Ankify Roam

A command-line tool which brings flashcards created in [Roam](https://roamresearch.com/) to [Anki](https://apps.ankiweb.net/).

<img src="images/anki_roam_screenshot.png">


## Main Features

- Create Front/Back and Cloze deletion flashcards in Roam and import to Anki.
- Hide or change the color of the cloze deletion markup in Roam.
- Supports block references, images, and aliases.
- Make edits in Roam to flashcards you've already imported and sync the changes to Anki. 
- Uses similar HTML syntax to Roam so you can style your Anki cards just like you do Roam.

## Content
1. [Installation](#Installation)
1. [Requirements](#Requirements)
1. [Basic Usage](#Basic-Usage)
1. [Options](#Options)
1. [Customizations](#Customizations)



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

Ankify a block by adding the #ankify tag to it. The tag must be included in the block itself, *it cannot be inherited from it's parents.*

By default, the block will be converted into a front/back style Anki note with the block content on the front and it's children on the back:

> - What is the capital of France? #ankify
>     - Paris

If the block includes any [cloze deletions](https://docs.ankiweb.net/#/editing?id=cloze-deletion), ankify_roam converts it to a cloze style Anki note. Add a cloze deletion by surrounding the text in curly brackets: 

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

All cloze ids like the following are supported by ankify_roam: "c1:", "c1|", "1:" 


### 2. Export Roam

Once you've tagged all the blocks to ankify, export your Roam: 
1. Click on the "more options" button in the top right corner of Roam.
2. Select Export All > JSON > Export All to export your Roam graph.
3. Unzip the downloaded file.

### 3. Open Anki

Open Anki. Make sure you're on the profile you'd like to add the cards to and that you've installed the [AnkiConnect](https://github.com/FooSoft/anki-connect) add-on.

### 4. Create Roam specific note types (first time only) 

Run the following to create 2 new note types in Anki for your Roam flashcards: 'Roam Basic' and 'Roam Cloze'
```
ankify_roam init
```
### 5. Add the Roam export to Anki

Replace "my_roam.json" with the filename of the json within the zip you downloaded in [step 2](#2.-Export-Roam).

```
ankify_roam add my_roam.json
```

Your flashcards should now be in Anki! 

### 6. Repeat

Whenever you create new flashcards in Roam or edit the existing ones, repeat these same steps to update Anki with the changes.  

## Options

### Roam Export Path

The Roam export path can refer to the json, the zip containing the json, or the directory which the zip is in. When a directory is given, ankify_roam will find and add the latest export in it. In my case, all 3 of these commands do the same thing:
```
ankify_roam add my_roam.json
ankify_roam add Roam-Export-1592525007321.zip
ankify_roam add ~/Downloads
```

### Choose a different ankify tag, deck, and note types

To use a tag other than #ankify to flag flashcards, pass the tag name to `--tag-ankify`: 
```
ankify_roam add --tag-ankify=flashcard my_roam.json
```  

To specify different note types, pass the note types names to `--default-basic` and `--default-cloze` (see [Custom Anki note types](#Create-custom-note-types) for details):
```
ankify_roam add --default-basic="My Basic" --default-cloze="My Cloze" my_roam.json
``` 

To specify a default deck other than "Default", pass the deck name to `--deck`:
```
ankify_roam add --deck="Biology" my_roam.json
```

You can also specify the deck and note type on a per-card basis using tags in Roam. This will override the default deck and note type specified at the command line:

- 2+2={4} #[[[[ankify]]:deck=Math]] #[[[[ankify]]:model=My Math Cloze]]

### Uncloze Namespace

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

As mentioned in the [options](#Options) section, you can import to different note types than the default 'Roam Basic' and 'Roam Cloze' types provided. Those note types will need to satisfy 2 requirements to be compatible with ankify_roam:   

1. **Include at least 2 fields for the basic note type and 1 for the cloze**. When ankify_roam is converting a block into an Anki note, it takes the content of the block and places it into the first field of the Anki note. For front/back flashcards, it also takes the children of the block and adds them to the second field of the Anki note. 

1. **Include an additional field called "uid"**. In addition to those fields, a "uid" field is required. This field is used by ankify_roam to remember which block in Roam corresponds with which note in Anki. Without this field, when you make a change to a block in Roam, ankify_roam will add that block as a new note in Anki rather than updating the existing one.

If you'd like to customize the style of the provided note types but you're new to creating note types in Anki, I'd suggest you create [clones](https://docs.ankiweb.net/#/editing?id=adding-a-note-type) of the 'Roam Basic' and 'Roam Cloze' note types provided and then just [edit the style](https://www.youtube.com/watch?v=F1j1Zx0mXME&yt:cc=on) of the clones.

### CSS ideas for your Anki cards

Hide all Roam tags (eg. the #ankify tag)
```
.rm-page-ref-tag {
    display: none;
}
```

Hide page reference brackets.
```
.rm-page-ref-brackets {
    display: none;
}
```

When a block has multiple children, they're added as bullet points on the backside of a card. If you'd prefer not to show the bullets, similar to the "View as Document" option in Roam, use the following CSS:
```
li {
    list-style-type: none;
}
```


### Add color or hide cloze deletions in Roam

You also define cloze deletions using curly bracket in page links:

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

Note: Just like the regular cloze markup, the page links can also include cloze ids eg. [[{c1:]]Paris[[}]] 