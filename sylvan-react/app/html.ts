// http(s) addresses and bare www. ones, stopping before trailing punctuation
const URL_PATTERN = /\b(?:https?:\/\/|www\.)[^\s<]+[^\s<.,;:!?'")\]]/gi;

/**
 * Turns web addresses written as plain text into links that open in a new tab. Text
 * that's already inside a link is left alone.
 */
export function linkifyHtml(html: string): string {
  const body = new DOMParser().parseFromString(html, 'text/html').body;
  const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
  const textNodes: Text[] = [];
  while (walker.nextNode()) {
    const text = walker.currentNode as Text;
    if (!text.parentElement?.closest('a')) textNodes.push(text);
  }

  for (const text of textNodes) {
    const matches = [...text.data.matchAll(URL_PATTERN)];
    if (matches.length === 0) continue;
    const fragment = document.createDocumentFragment();
    let last = 0;
    for (const match of matches) {
      const start = match.index;
      fragment.append(text.data.slice(last, start));
      const link = document.createElement('a');
      link.href = match[0].startsWith('www.') ? `https://${match[0]}` : match[0];
      link.target = '_blank';
      link.rel = 'noopener noreferrer nofollow';
      link.textContent = match[0];
      fragment.append(link);
      last = start + match[0].length;
    }
    fragment.append(text.data.slice(last));
    text.replaceWith(fragment);
  }
  return body.innerHTML;
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * Deck descriptions as HTML. Most are plain text, and HTML would run any line breaks
 * in them together, so blank lines become paragraphs and single line breaks become
 * <br>s. Descriptions that already contain HTML tags are returned as they are.
 */
export function descriptionHtml(description: string): string {
  if (/<[a-z][^>]*>/i.test(description)) return description;
  return description
    .split(/\r?\n\s*\r?\n/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
    .map((paragraph) => `<p>${escapeHtml(paragraph).replace(/\r?\n/g, '<br>')}</p>`)
    .join('');
}
