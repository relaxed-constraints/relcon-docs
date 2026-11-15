# Images and figures

Use an image file for a photograph, plot, screenshot or exported illustration.
Unlike a Mermaid block, the SVG below is a static file included in the site.
It illustrates a workflow; it does not present measured results.

## A basic image

A Markdown image uses an exclamation mark, alternative text and a path:

```markdown
![Data feeds an experiment, which produces results for analysis.](images/research-workflow.svg)
```

![Data feeds an experiment, which produces results for analysis.](images/research-workflow.svg)

Paths are relative to the Markdown page. Describe the image's meaning in the
alternative text so readers can understand it without seeing the image.

## A figure with a caption

Use HTML's `figure` and `figcaption` elements when an image needs a caption.
The shared stylesheet makes figures responsive and separates the caption from
the image. Captions are written explicitly; numbering is not automatic.

```html
<figure>
  <img src="images/research-workflow.svg"
       alt="Data feeds an experiment, which produces results for analysis."
       width="900" height="240">
  <figcaption>Figure 1. A simple research workflow: prepare data, run an experiment, and inspect results.</figcaption>
</figure>
```

<figure>
  <img src="images/research-workflow.svg"
       alt="Data feeds an experiment, which produces results for analysis."
       width="900" height="240">
  <figcaption>Figure 1. A simple research workflow: prepare data, run an experiment, and inspect results.</figcaption>
</figure>

Zensical resolves both Markdown images and these HTML image sources relative to
the source page, then rewrites their URLs for the published site.

## Local files and web images

Keep important figures under `docs/images/` so they are versioned and published
with the documentation. PNG and JPEG work well for photographs and screenshots;
SVG stays sharp for plots and illustrations.

A web URL also works:

```markdown
![Description of the image](https://example.org/image.png)
```

That URL is illustrative. A real remote image must remain publicly accessible,
permit embedding, and have suitable usage rights. Its availability depends on
the external host; local images do not have that dependency.
