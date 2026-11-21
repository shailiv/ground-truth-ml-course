// The sign-in page's only script. Shows the "wrong passphrase" line, and keeps a deep link alive: the address
// fragment (#/lesson/3-2) is not sent to the server, but a browser carries it across the redirects if the form
// posts to an address that still has it.
if (new URLSearchParams(location.search).has("wrong")) document.getElementById("wrong").hidden = false;
if (/^#\/[\w\/-]*$/.test(location.hash)) document.querySelector("form").action = "/login" + location.hash;
