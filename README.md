# Ankify Roam

A command-line tool for importing flashcards from Roam into Anki.

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

In Roam, tag blocks which you want to import to anki with #ankify. By default, the block is converted to a Basic card:
- What is the capitol of France? #ankify
    - Paris

If you add a cloze deletion with curly brackets, then it'll become a Cloze card:
- {Paris} is the capital of France #ankify 

When you're ready to ankify your roam, export your roam db: 
1. Click on the ... in the top right corner
2.  Select Export All > JSON > Export All

Open Anki.

Run the following to create 2 new card types in Anki: 'Roam Basic' and 'Roam Cloze'
```
ankify_roam setup
```

Run ankify_roam on your Roam export to create your anki cards:
```
ankify_roam Roam-Export-1592174304830.zip
```
The blocks you tagged in Roam should now be in Anki!

### Updating and creating new cards

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

### Examples


## Details

- TODO: stuff which the package can't do
    - empty cards
    - delete cards from anki that have been deleted from roam
    - change the deck (and type?) of a card after it's been uploaded 
        - you _can_ change the fields though

- All cloze types should have '[Cc]loze' somewhere in the name

### Marking up Roam

#### Cloze markup

#### Child blocks


