
## Parents

### Hide all

```css
.parent {
    display: none;
}
```

### Parents and page title as breadcrumbs
```css
.parent {
    display: inline-block;
    padding-bottom: 10px;
    font-size: 15px;
}
.parent::after {
    content: "›";
}
```

### Center title and parents as breadcrumbs
```css
.parent.block {
    display: inline-block;
    padding-bottom: 10px;
    font-size: 15px;
}
.parent.block::after {
    content: "›";
}
```

### Stacked and indented 
```css
.card {
    text-align: left;
}

.block::before {
    content: "•";
    margin-right: 10px;
}

.block {
    margin-left: calc(20px * var(--data-lvl));
}
```