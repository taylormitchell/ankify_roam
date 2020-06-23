
## Anki

Hide all Roam tags 
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

## Roam


```css
span[data-link-title="{"] > span,
span[data-link-title="}"] > span
{
  color: #DDDCDC !important;
}
```