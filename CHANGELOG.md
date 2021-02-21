# Changelog

## [0.1.0]

### Added
- Add `show-parents` option. This option controls the number of parent blocks to include with your card. Set `show-parents=1` to include only the direct paretn, `show-parents=2` to include parent and grandparent, etc. You can also show all parents by setting `show-parents=True` or no parents by setting `show-parents=False`. By default, show-parents is set to 1  
- Add `max-depth` option. Set `max-depth=1` to only includes an ankified blocks children, `max-depth=2` only include children and their children, etc. By default, `max-depth=None` which includes all levels of children.
- Add clozify.js, a [[roam/js]] script for creating roam style cloze markup

### Changed
- Hide ankify tag and options by default

### Fixed
- Fix display of in-block newlines 
