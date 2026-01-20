# Witt Node

This directory contains source code for the node system.

```txt
.node-editor (NodeEditor::Gtk.ScrolledWindow)
└── .node-canvas (NodeEditor.Canvas::Gtk.Fixed)
    ├── .node-frame (NodeFrame::Gtk.Box)
    │   ├── .node-head (NodeFrame.Head::Gtk.Box)
    │   │   └── .node-title (NodeFrame.Title::Gtk.Label)
    │   └── .node-body (NodeFrame.Body::Gtk.Box)
    │       ├── .node-content (NodeContent::Gtk.Widget)
    │       │    ├── [.node-socket] (NodeContent.Socket.Gtk.Widget)
    │       │    ├── .node-widget (NodeContent.Widget::Gtk.Widget)
    │       │    └── [.node-socket] (NodeContent.Socket.Gtk.Widget)
    │       └── .node-content (NodeContent::Gtk.Widget)
    └── .node-frame (NodeFrame::Gtk.Box)
```