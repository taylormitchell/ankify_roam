// Wrap selected text in cloze brackets

function clozifySelectedText() {
    var txtArea = document.activeElement;
    if (txtArea.selectionStart != undefined) {
      var startPos = txtArea.selectionStart;
      var endPos = txtArea.selectionEnd;
      selectedText = txtArea.value.substring(startPos, endPos);
      txtArea.value = txtArea.value.slice(0, startPos) + '[[{]]' + selectedText + '[[}]]' + txtArea.value.slice(endPos); 
      txtArea.selectionEnd= endPos + 2*'[[{]]'.length;
    }
}
  
document.onkeydown = function(e) {
  if (e.shiftKey && e.metaKey && e.key == "z") {
    clozifySelectedText();
  }
};