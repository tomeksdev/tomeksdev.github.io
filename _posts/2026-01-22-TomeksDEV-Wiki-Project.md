---
title: Build a Static Markdown Wiki with Jekyll — TomeksDEV Wiki Project
description: Learn how to build a fast, customizable, and static Markdown-based wiki using Jekyll. Ideal for public documentation, tutorials, and open knowledge sharing.
author: vujca
date: 2026-01-22 17:06:00 +0100
categories: [Programming]
tags: [Jekyll wiki, Markdown documentation, static site generator, GitHub Pages wiki, open-source documentation, developer wiki, project documentation,Jekyll tutorial]
image:
  path: /assets/img/post/TomeksDEV-wiki/wiki.png
  alt: TomeksDEV Wiki
---
Looking for a **lightweight, Markdown‑based wiki** that’s fast, customizable, and easy to maintain? The **TomeksDEV Wiki project** is a developer‑friendly, scalable solution powered entirely by **Jekyll**. It offers clean, login‑free access to documentation — perfect for open knowledge sharing, internal wikis, or technical manuals.

In this guide, you’ll learn **why this static wiki engine was built**, **how it’s structured**, and **how to set it up and deploy it yourself** — with detailed examples and a walkthrough of its architecture.

👉 Explore the full source code:  
🔗 [https://github.com/tomeksdev/wiki](https://github.com/tomeksdev/wiki)  
🌐 Live demo: [https://doc.tomeksdev.com/](https://doc.tomeksdev.com/)

---

## Why Use Jekyll for a Developer Wiki?

There are many documentation tools out there — BookStack, Wiki.js, MediaWiki — so why go with **Jekyll**?

- **Zero-friction publishing:** No logins or user accounts — content is public by default.
- **Write in Markdown:** Create pages in your favorite text editor or IDE.
- **Static hosting support:** Works with GitHub Pages, Netlify, Cloudflare Pages, and more.
- **Fully customizable:** You control layouts, styles, and UI components.

Perfect for **technical documentation**, **developer handbooks**, **API docs**, or **public guides** where speed and simplicity matter.

---

## Jekyll Wiki Architecture Overview

This project uses **Jekyll**, a static site generator that transforms Markdown into static HTML files. Key features:

- Content written in Markdown
- Navigation powered by front‑matter metadata
- No backend or server logic — just static files

```
┌─────────────────┐          ┌───────────────┐
│ _docs, _shelves │ Markdown │   Jekyll      │ → Static HTML
│ _projects files │    +     │  Build Engine │ 
└─────────────────┘          └───────────────┘
                                      ↓
                            Hosted (GitHub Pages / CDN)
```

---

## Project Folder Structure

When you clone the repository, here’s what you get:

```
wiki/
├── _config.yml
├── _projects/
├── _shelves/
├── _docs/
├── _layouts/
├── assets/
├── _data/
├── index.md
├── README.md
└── ...
```

---

**🔹 `_projects/` — Define Main Wiki Sections**

Use this folder to define major project areas. Each file becomes a top‑level entry in the sidebar.


**🔹 `_shelves/` — Subsections Within Projects**

Shelves work like chapters. They help organize related documentation within a project.


**🔹 `_docs/` — Your Actual Wiki Pages**

These are the individual Markdown files that make up your wiki. Each doc links to a project and shelf for navigation.

---

## Jekyll Configuration

Main options in `_config.yml`:

```yaml
project_mode: multi           # or single
default_project_id: wiki
```

- `multi` mode = multiple projects in the sidebar
- `single` mode = one unified documentation set

---

## Layout Templates

Located in `_layouts/`, these templates control page rendering:

| Layout         | Purpose                                 |
|----------------|-----------------------------------------|
| `default.html` | Global layout with header/sidebar       |
| `project.html` | Displays shelves for a project          |
| `shelf.html`   | Lists docs in a shelf                   |
| `doc.html`     | Shows individual content pages          |

---

## Local Setup Instructions

Run the wiki locally for editing:

```bash
git clone https://github.com/tomeksdev/wiki.git
cd wiki
bundle install
bundle exec jekyll serve --livereload
```

## Real‑World Project Example

Sample file layout:

```
_projects/cli-tool.md
_shelves/installation.md
_docs/installation.md
_docs/usage.md
_docs/advanced.md
```

This builds a sidebar and content flow automatically.

---

## Sidebar Navigation Explained

In **multi-project** mode:

```
[Home]
├─ Project A
│   ├─ Shelf 1
│   ├─ Shelf 2
├─ Project B
│   ├─ Shelf 1
```

In **single-project** mode:

```
[Home]
├─ Shelf 1
├─ Shelf 2
```

---

## Tips & Common Issues

- Ensure `parent_shelf` matches `shelf_id`
- Use numerical ordering (`order: 1`, `order: 2`, etc.)
- Reference the correct layout in front matter

---

## Conclusion: Build Your Own Markdown Wiki

The **TomeksDEV Jekyll Wiki** offers a clean, high-performance alternative to complex documentation platforms.

📌 *View the live wiki or fork the GitHub repo to get started today!*  
🔗 [https://github.com/tomeksdev/wiki](https://github.com/tomeksdev/wiki)  
🌐 [https://doc.tomeksdev.com/](https://doc.tomeksdev.com/)