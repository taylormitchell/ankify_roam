# Ankify Roam

A command-line tool which brings flashcards created in [Roam](https://roamresearch.com/) to [Anki](https://apps.ankiweb.net/).

<table border=0px>
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

<div style="width: 100%; overflow: hidden;">
    <div style="width: 300px; float: left;">
        <img src="images/roam_screenshot.png">
    </div>
    <div style="width: 300px; float: left;">
        <img src="images/anki_screenshot.png">
    </div>
</div>

## Main Features

- Create Front/Back or Cloze deletion flashcards. 
- Edit flashcards in Roam and bring those changes over to Anki. 
- Supports block references, images, and aliases.
- Add style to your Anki cards just like in Roam.

## Contents
1. [What it is](#What-it-is)
1. [Main Features](#Main-Features)
1. [Contents](#Contents)
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

Define a card by adding the #ankify tag. By default the block will be converted into a Basic note type with the block content on the front and it's children on the back: 

> - What is the capital of France? #ankify
>     - Paris

Use curly brackets to define cloze deletions. Whenever a block tagged with #ankify includes a cloze deletion, ankify_roam converts it to a Cloze note type. 

> {Paris} is the capital and most populous city of {France}, with a estimated population of {2,148,271} residents #ankify

You can explicitely define the cloze ids or have ankify_roam infer them. Here's an example showing what cloze markup in Roam becomes in Anki:


<table border=0px>
<tr>
<td>
        <div>{1:Paris} is the capital and most populous city of {2:France}, with a estimated population of {2,148,271} residents #ankify</div>
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

### 4. Create Roam specific card types 

**First time only**: Run the following to create 2 new card types in anki for your Roam flashcards: 'Roam Basic' and 'Roam Cloze'
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

## Options

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

#### Block Level Settings   

Specify the deck and note type on a per-card basis: 

- 2+2={4} #[[[[ankify]]:deck=Math]] #[[[[ankify]]:model=My Cloze]]

#### Uncloze Namespace

When you add a cloze deletion around a namespaced page reference, you have the option to leave the namespace out of it: 
```
ankify_roam add --pageref-cloze=base_only my_roam.json
```

With that option, a cloze deletion like this in Roam...

<img src="images/pageref_cloze_roam.png" width=600px>

...will look like this in Anki:

<img src="images/pageref_cloze_anki.png" width=500px>

Note that instead of the entire [[Design Pattern/Adaptor Pattern]] page reference getting cloze-deleted, only the base name in the page title is.

TODO: cover all features in this section so that I don't need a separate documentation section

## Customizations

### Custom Anki note types

The Anki notes created by ankify_roam use very similar html elements and classes to Roam. You should be able to bring over much of the CSS you have for your Roam over to Anki.  

If you do want to change the styling of your Anki notes, I'd suggest creating and then modifying the 'Roam Basic' and 'Roam Cloze' types provided, or making copies of those note types. 

To create the 'Roam Basic' and 'Roam Cloze' note types, run the following while Anki is open:
```
ankify_roam init
``` 
If you want to make a copy of these type, do the following in Anki:
- Go to Tools > Manage Note Types
- Click "Add"
- Select "Clone: Roam Basic" (or "Clone: Roam Cloze")

#### Style 

Whether you're modifying 'Roam Basic' and 'Roam Cloze' directly or modifying copies of them, you can change the CSS without worrying about compatibility issues 

If you want to change the note type fields, there are a few things to keep in mind: 

#### Fields

##### The "uid" field
The "uid" field is used by ankify_roam to remember which block in Roam corresponds with which note in Anki. Without this field, when you make a change to a block in Roam, ankify_roam will add that block as a new note in Anki rather than updating the existing one.

##### Blocks to Anki fields
When ankify_roam is converting a block into an Anki note, it takes the content of the block and places it into the first field of the Anki note. In the case of a Basic type, additionally the children of the block are added to the second field of the Anki note. 


### Styling cloze deletions in Roam

You can also use curly bracket page links to define cloze deletions:

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



