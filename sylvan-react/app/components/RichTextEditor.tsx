import React, { useState } from 'react';
import { EditorContent, useEditor, useEditorState, type Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';

function ToolbarButton({
  label,
  icon,
  text,
  active = false,
  disabled = false,
  onClick,
}: {
  label: string;
  icon?: string;
  text?: string;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`rich-text-button ${active ? 'is-active' : ''}`}
      title={label}
      aria-label={label}
      aria-pressed={active}
      disabled={disabled}
      // Keeps the editor's selection while the button is clicked
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
    >
      {icon ? <i className={`fa ${icon}`} aria-hidden="true" /> : text}
    </button>
  );
}

function LinkForm({ editor, onDone }: { editor: Editor; onDone: () => void }) {
  const [url, setUrl] = useState<string>(editor.getAttributes('link').href ?? '');

  function apply() {
    const chain = editor.chain().focus().extendMarkRange('link');
    if (url.trim()) chain.setLink({ href: url.trim() }).run();
    else chain.unsetLink().run();
    onDone();
  }

  return (
    <div className="rich-text-link-form">
      <input
        type="url"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://… (leave empty to remove the link)"
        aria-label="Link address"
        autoFocus
        onKeyDown={(e) => {
          // Enter would otherwise submit the deck form
          if (e.key === 'Enter') {
            e.preventDefault();
            apply();
          } else if (e.key === 'Escape') {
            e.preventDefault();
            onDone();
            editor.commands.focus();
          }
        }}
      />
      <button type="button" className="action-button" onClick={apply}>
        Apply
      </button>
      <button type="button" className="action-button" onClick={onDone}>
        Cancel
      </button>
    </div>
  );
}

function Toolbar({ editor }: { editor: Editor }) {
  const [editingLink, setEditingLink] = useState(false);
  // The toolbar re-renders as the selection moves, so active buttons stay in sync
  const state = useEditorState({
    editor,
    selector: ({ editor: e }) => ({
      bold: e.isActive('bold'),
      italic: e.isActive('italic'),
      h2: e.isActive('heading', { level: 2 }),
      h3: e.isActive('heading', { level: 3 }),
      bulletList: e.isActive('bulletList'),
      orderedList: e.isActive('orderedList'),
      link: e.isActive('link'),
      canUndo: e.can().undo(),
      canRedo: e.can().redo(),
    }),
  });
  const chain = () => editor.chain().focus();

  return (
    <>
      <div className="rich-text-toolbar" role="toolbar" aria-label="Formatting">
        <ToolbarButton
          label="Bold"
          icon="fa-bold"
          active={state.bold}
          onClick={() => chain().toggleBold().run()}
        />
        <ToolbarButton
          label="Italic"
          icon="fa-italic"
          active={state.italic}
          onClick={() => chain().toggleItalic().run()}
        />
        <span className="rich-text-separator" />
        <ToolbarButton
          label="Heading"
          text="H2"
          active={state.h2}
          onClick={() => chain().toggleHeading({ level: 2 }).run()}
        />
        <ToolbarButton
          label="Subheading"
          text="H3"
          active={state.h3}
          onClick={() => chain().toggleHeading({ level: 3 }).run()}
        />
        <span className="rich-text-separator" />
        <ToolbarButton
          label="Bulleted list"
          icon="fa-list-ul"
          active={state.bulletList}
          onClick={() => chain().toggleBulletList().run()}
        />
        <ToolbarButton
          label="Numbered list"
          icon="fa-list-ol"
          active={state.orderedList}
          onClick={() => chain().toggleOrderedList().run()}
        />
        <ToolbarButton
          label="Link"
          icon="fa-link"
          active={state.link || editingLink}
          onClick={() => setEditingLink((v) => !v)}
        />
        <span className="rich-text-separator" />
        <ToolbarButton
          label="Undo"
          icon="fa-undo"
          disabled={!state.canUndo}
          onClick={() => chain().undo().run()}
        />
        <ToolbarButton
          label="Redo"
          icon="fa-repeat"
          disabled={!state.canRedo}
          onClick={() => chain().redo().run()}
        />
      </div>
      {editingLink && <LinkForm editor={editor} onDone={() => setEditingLink(false)} />}
    </>
  );
}

/**
 * A rich text editor that reads and writes HTML. The initial value is only read once, so
 * remount it (with a key) to load different content.
 */
export default function RichTextEditor({
  labelId,
  initialValue,
  onChange,
}: {
  // The id of the element labelling the editor
  labelId: string;
  initialValue: string;
  onChange: (html: string) => void;
}) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [2, 3] },
        code: false,
        codeBlock: false,
        link: { openOnClick: false, autolink: true, defaultProtocol: 'https' },
      }),
    ],
    content: initialValue,
    // The SPA build pre-renders the page shell without a DOM
    immediatelyRender: false,
    editorProps: {
      attributes: {
        class: 'rich-text rich-text-content',
        role: 'textbox',
        'aria-multiline': 'true',
        'aria-labelledby': labelId,
      },
    },
    // An empty editor still holds an empty paragraph, which shouldn't be saved
    onUpdate: ({ editor: e }) => onChange(e.isEmpty ? '' : e.getHTML()),
  });

  return (
    <div className="rich-text-editor">
      {editor && <Toolbar editor={editor} />}
      <EditorContent editor={editor} />
    </div>
  );
}
