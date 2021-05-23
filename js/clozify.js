// Wrap selected text in cloze brackets

function clozifySelectedText(ankifyTag="#ankify", addClozeId=true) {
  var sep = ""
  var txtArea = document.activeElement;

  if (txtArea.selectionStart != undefined) {
    // Select text
    var startPos = txtArea.selectionStart;
    var endPos = txtArea.selectionEnd;
    selectedText = txtArea.value.substring(startPos, endPos);
    // Choose cloze id
    if (!addClozeId) {
      var nextClozeId = '';
    } else {
      var pat = /\[\[{(\d+)\]\]/g;
      var existingClozeIds = [...txtArea.innerHTML.matchAll(pat)].map(el => Number(el[1]));
      if (existingClozeIds.length === 0) {
        var nextClozeId = 1;
      } else {
        var nextClozeId = Math.max(...existingClozeIds) + 1;
      }
    }
    // Wrap text in cloze brackets
    clozifiedText = txtArea.value.slice(0, startPos) + `[[{${nextClozeId}]]` + selectedText + '[[}]]' + txtArea.value.slice(endPos);
    // Add ankify tag
    if (txtArea.value.indexOf(ankifyTag)==-1){
      clozifiedText = clozifiedText + sep + ankifyTag
    }
    
    var valueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
    valueSetter.call(txtArea, clozifiedText);
    txtArea.selectionEnd = endPos + `[[${nextClozeId}]]`.length + '[[}]]'.length

    var inputEvent = new Event('input', { bubbles: true});
    txtArea.dispatchEvent(inputEvent);

  }
}

document.onkeydown = function(e) {
  let ankifyTag = "#ankify"
  let addClozeId = true
  if (e.shiftKey && e.metaKey && e.key == "z") {
    clozifySelectedText(ankifyTag, addClozeId);
  }
};