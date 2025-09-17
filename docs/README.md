# CodeQL Wrapper Documentation

This directory contains the Docusaurus-powered documentation site for CodeQL Wrapper.

## 🚀 Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/en/download/) version 18.0 or above
- npm or yarn package manager

### Installation

```bash
cd docs
npm install
```

### Local Development

```bash
npm start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.

### Build

```bash
npm run build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service.

## 📁 Project Structure

```
docs/
├── blog/                     # Blog posts
│   ├── authors.yml          # Blog authors
│   └── *.md                 # Blog post files
├── docs/                    # Documentation pages
│   ├── intro.md            # Getting started
│   ├── installation.md     # Installation guide
│   ├── cli-usage.md        # CLI reference
│   ├── cicd-integration.md # CI/CD integration
│   └── api.md              # API reference
├── src/                     # Custom React components
├── static/                  # Static files (images, etc.)
├── docusaurus.config.js     # Site configuration
├── sidebars.js             # Sidebar configuration
└── package.json            # Dependencies
```

## ✏️ Contributing to Documentation

### Adding a New Page

1. Create a new markdown file in the `docs/` directory
2. Add frontmatter at the top:
   ```yaml
   ---
   sidebar_position: 3
   ---
   ```
3. Update `sidebars.js` if needed
4. Write your content in Markdown

### Adding a Blog Post

1. Create a new markdown file in the `blog/` directory
2. Name it with the date format: `YYYY-MM-DD-post-title.md`
3. Add frontmatter:
   ```yaml
   ---
   slug: post-slug
   title: Post Title
   authors: [author-key]
   tags: [tag1, tag2]
   ---
   ```

### Markdown Features

Docusaurus supports extended Markdown features:

#### Code Blocks with Syntax Highlighting

```python
# Python code example
codeql_wrapper.analyze('/path/to/repo')
```

#### Admonitions

:::tip Pro Tip
Use `--verbose` flag for detailed output during debugging.
:::

:::warning
Make sure to set the `GITHUB_TOKEN` environment variable for SARIF uploads.
:::

:::danger
Never commit GitHub tokens to your repository!
:::

## 🎨 Customization

### Styling

Custom CSS can be added to `src/css/custom.css`.

### Components

Custom React components can be added to `src/components/`.

### Configuration

The main configuration is in `docusaurus.config.js`:

- Site metadata
- Theme configuration
- Plugin configuration
- Navbar and footer

## 🚀 Deployment

The documentation is automatically deployed to GitHub Pages when changes are pushed to the `main` branch in the `docs/` directory.

### Manual Deployment

```bash
npm run build
npm run serve
```

### GitHub Pages Setup

The site is configured to deploy to:
- URL: `https://tweag.github.io/codeql-wrapper/`
- Base URL: `/codeql-wrapper/`

## 📚 Resources

- [Docusaurus Documentation](https://docusaurus.io/)
- [Markdown Guide](https://www.markdownguide.org/)
- [MDX Documentation](https://mdxjs.com/)

## 🐛 Issues

If you find issues with the documentation:

1. Check existing [issues](https://github.com/tweag/codeql-wrapper/issues)
2. Create a new issue with the `documentation` label
3. Or submit a pull request with fixes

## 📝 License

The documentation is part of the CodeQL Wrapper project and follows the same MIT license.
