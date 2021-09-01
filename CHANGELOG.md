# Changelog

## 0.1.2 (2021-08-31)

### New Features
- Adding the #ankify-root tag to a block makes it so all descendent blocks which are ankified will only include parents up to the block with the #ankify-root tag

### Improvements
- Added more syntax for defining cloze hints e.g. "Example of {clozed text[[::]]hint}", "Example of {clozed text[[::hint]]}", "Example of [[{]]clozed text[[::hint}]]"

### Fixes
- Correctly parse more code block languages
- Option tags closest to block now prioritized

## 0.1.1 (2021-05-23)

### New Features
- Added support for hints e.g. "Javascript is {synchronous::asynchronous/synchronous}" in Roam becomes "Javascript is {{c1::synchronous::asynchronous/synchronous}}" in Anki
- Added support for block quotes

### Fixes
- Blocks with one child but many descendants now include all descendants 

## 0.1.0 (2021-04-11)

### Breaking Changes
- To improve the display of lists, the html structure of anki fields was changed. This requires users to update the css of their note types accordingly. If you use the default `Roam Basic` and `Roam Cloze` note types, then you can update their css using `ankify_roam init-models --overwrite`. Otherwise, use [roam_basic.css](css/roam_basic.css) and [roam_cloze.css](css/roam_cloze.css) as starting points to manually update your note type css.

### Fixes
- Parsing and display of italics, bold, underlines, and inline-code markup.
- Added [character escaping](https://www.w3.org/International/questions/qa-escapes#use). This fixed a parsing error which was leading to ankify_roam misidentifying blocks as duplicates and then failing to import them. 
- Display of in-block newlines.

### New Features
- Added `--num-parents` option. This option controls the number of parent blocks to include with your card. Set `--num-parents=1` to include only the parent directly above, `--num-parents=2` to include parent and grandparent, etc. Run `ankify_roam add --help` for details.
- Added `--include-page` option. This option controls whether to include the page title with your cards.
- Added `--max-depth` option. Set `--max-depth=1` to only includes blocks children but not grandchildren, `max-depth=2` to only include children and grandchildren but not great-grandchildren, etc. 
- Added clozify.js, a [[roam/js]] script. Once added to your Roam, selecting text and pressing `cmd-shift-z` will wrap the text in roam-style cloze markup (e.g. [[{]]list this[[}]]) and add an #ankify tag to the block.  

### Improvements
- CSS changes to `Roam Basic` and `Roam Cloze` note types:
    - Use [breadcrumb nagivation](https://www.w3schools.com/howto/howto_css_breadcrumbs.asp) style display for block parents.
    - Hide `#ankify` tag and inline options (e.g. hides `#[[ankify_roam: show-parents=True]]`).
    - Updated css to match the html changes [mentioned above](#Breaking-Changes).
    - Other minor css improvements.
